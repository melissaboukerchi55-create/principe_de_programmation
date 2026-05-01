"""Tests for enrollments — the M:N relation with attributes."""
import pytest


@pytest.fixture
def course_id(client, instructor_token):
    H = {"Authorization": f"Bearer {instructor_token}"}
    cat_id = client.post("/api/v1/categories", headers=H,
        json={"name": "Cat", "slug": "cat"}).json()["id"]
    return client.post("/api/v1/courses", headers=H,
        json={"title": "C", "category_id": cat_id, "published": True}).json()["id"]


def test_enroll_then_unenroll(client, student_token, course_id):
    H = {"Authorization": f"Bearer {student_token}"}
    r = client.post(f"/api/v1/courses/{course_id}/enroll", headers=H)
    assert r.status_code == 201
    body = r.json()
    assert body["progress"] == 0
    assert body["rating"] is None

    r = client.delete(f"/api/v1/courses/{course_id}/enroll", headers=H)
    assert r.status_code == 204


def test_duplicate_enrollment_409(client, student_token, course_id):
    H = {"Authorization": f"Bearer {student_token}"}
    client.post(f"/api/v1/courses/{course_id}/enroll", headers=H)
    r = client.post(f"/api/v1/courses/{course_id}/enroll", headers=H)
    assert r.status_code == 409


def test_update_progress_and_rating(client, student_token, course_id):
    H = {"Authorization": f"Bearer {student_token}"}
    client.post(f"/api/v1/courses/{course_id}/enroll", headers=H)
    r = client.patch(f"/api/v1/courses/{course_id}/enroll", headers=H,
        json={"progress": 75, "rating": 4})
    assert r.status_code == 200
    assert r.json()["progress"] == 75
    assert r.json()["rating"] == 4


@pytest.mark.parametrize("bad", [{"rating": 0}, {"rating": 6}, {"progress": -1},
                                  {"progress": 101}])
def test_validation_bounds(client, student_token, course_id, bad):
    H = {"Authorization": f"Bearer {student_token}"}
    client.post(f"/api/v1/courses/{course_id}/enroll", headers=H)
    r = client.patch(f"/api/v1/courses/{course_id}/enroll", headers=H, json=bad)
    assert r.status_code == 422


def test_instructor_cannot_enroll(client, instructor_token, course_id):
    H = {"Authorization": f"Bearer {instructor_token}"}
    r = client.post(f"/api/v1/courses/{course_id}/enroll", headers=H)
    assert r.status_code == 403


def test_my_enrollments_returns_full_course_info(client, student_token, course_id):
    H = {"Authorization": f"Bearer {student_token}"}
    client.post(f"/api/v1/courses/{course_id}/enroll", headers=H)
    r = client.get("/api/v1/users/me/enrollments", headers=H)
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["course"]["id"] == course_id
    assert "category" in items[0]["course"]
    assert "instructor" in items[0]["course"]


def test_owner_can_list_students(client, instructor_token, student_token, course_id):
    Hs = {"Authorization": f"Bearer {student_token}"}
    Hi = {"Authorization": f"Bearer {instructor_token}"}
    client.post(f"/api/v1/courses/{course_id}/enroll", headers=Hs)
    client.patch(f"/api/v1/courses/{course_id}/enroll", headers=Hs,
                 json={"progress": 30, "rating": 5})
    r = client.get(f"/api/v1/courses/{course_id}/students", headers=Hi)
    assert r.status_code == 200
    students = r.json()
    assert len(students) == 1
    assert students[0]["student_email"] == "student@test.com"
    assert students[0]["progress"] == 30
    assert students[0]["rating"] == 5
