"""Tests for courses, lessons (1:N), and categories."""
import pytest


@pytest.fixture
def category_id(client, instructor_token):
    r = client.post("/api/v1/categories",
        headers={"Authorization": f"Bearer {instructor_token}"},
        json={"name": "Test Cat", "slug": "test-cat"})
    assert r.status_code == 201
    return r.json()["id"]


def test_student_cannot_create_category(client, student_token):
    r = client.post("/api/v1/categories",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"name": "X", "slug": "x"})
    assert r.status_code == 403


def test_create_course_then_get_with_lessons(client, instructor_token, category_id):
    H = {"Authorization": f"Bearer {instructor_token}"}
    # create course
    r = client.post("/api/v1/courses", headers=H,
        json={"title": "C1", "category_id": category_id, "published": True})
    assert r.status_code == 201
    cid = r.json()["id"]

    # add 2 lessons
    for pos in [2, 1]:  # out of order to verify ordering
        r = client.post(f"/api/v1/courses/{cid}/lessons", headers=H,
            json={"title": f"L{pos}", "position": pos, "duration_min": 10})
        assert r.status_code == 201

    # detail must include both, sorted by position
    r = client.get(f"/api/v1/courses/{cid}")
    assert r.status_code == 200
    lessons = r.json()["lessons"]
    assert [l["position"] for l in lessons] == [1, 2]


def test_patch_course_only_changes_provided_fields(client, instructor_token, category_id):
    H = {"Authorization": f"Bearer {instructor_token}"}
    cid = client.post("/api/v1/courses", headers=H,
        json={"title": "Orig", "description": "DescA", "category_id": category_id,
              "published": False}).json()["id"]
    r = client.patch(f"/api/v1/courses/{cid}", headers=H, json={"published": True})
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "Orig"  # untouched
    assert body["description"] == "DescA"  # untouched
    assert body["published"] is True  # changed


def test_non_owner_cannot_update_course(client, instructor_token, category_id):
    H = {"Authorization": f"Bearer {instructor_token}"}
    cid = client.post("/api/v1/courses", headers=H,
        json={"title": "Owned", "category_id": category_id}).json()["id"]

    # second instructor
    r = client.post("/api/v1/auth/register", json={
        "email": "other@test.com", "password": "supersecret1",
        "full_name": "Other", "role": "instructor"})
    other_tk = r.json()["access_token"]

    r = client.patch(f"/api/v1/courses/{cid}",
        headers={"Authorization": f"Bearer {other_tk}"},
        json={"title": "Hacked"})
    assert r.status_code == 403


def test_delete_course_cascades_to_lessons(client, instructor_token, category_id):
    H = {"Authorization": f"Bearer {instructor_token}"}
    cid = client.post("/api/v1/courses", headers=H,
        json={"title": "DelMe", "category_id": category_id}).json()["id"]
    lesson_id = client.post(f"/api/v1/courses/{cid}/lessons", headers=H,
        json={"title": "L", "position": 1}).json()["id"]

    r = client.delete(f"/api/v1/courses/{cid}", headers=H)
    assert r.status_code == 204
    # course gone
    assert client.get(f"/api/v1/courses/{cid}").status_code == 404
    # lesson cascaded — try update on the orphan
    r = client.put(f"/api/v1/lessons/{lesson_id}", headers=H, json={"title": "z"})
    assert r.status_code == 404


def test_filter_courses_by_category(client, instructor_token, category_id):
    H = {"Authorization": f"Bearer {instructor_token}"}
    # second category
    cat2 = client.post("/api/v1/categories", headers=H,
        json={"name": "Other", "slug": "other"}).json()["id"]
    client.post("/api/v1/courses", headers=H,
        json={"title": "A", "category_id": category_id, "published": True})
    client.post("/api/v1/courses", headers=H,
        json={"title": "B", "category_id": cat2, "published": True})

    r = client.get(f"/api/v1/courses?category_id={category_id}")
    titles = [c["title"] for c in r.json()]
    assert titles == ["A"]
