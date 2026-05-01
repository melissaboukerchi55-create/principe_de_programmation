"""Tests for the 1:1 User <-> Profile relation."""


def test_get_me_includes_profile(client, student_token):
    H = {"Authorization": f"Bearer {student_token}"}
    r = client.get("/api/v1/users/me", headers=H)
    assert r.status_code == 200
    body = r.json()
    assert body["profile"] is not None
    assert body["profile"]["bio"] is None  # empty profile auto-created


def test_update_profile_persists_through_get_me(client, student_token):
    H = {"Authorization": f"Bearer {student_token}"}
    payload = {"bio": "Web learner", "github_url": "https://github.com/me"}
    r = client.put("/api/v1/users/me/profile", headers=H, json=payload)
    assert r.status_code == 200
    # Round-trip: read it back
    r = client.get("/api/v1/users/me", headers=H)
    profile = r.json()["profile"]
    assert profile["bio"] == "Web learner"
    assert profile["github_url"] == "https://github.com/me"


def test_unauthenticated_me_401(client):
    r = client.get("/api/v1/users/me")
    assert r.status_code == 401
