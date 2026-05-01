"""Tests for auth endpoints."""


def test_register_creates_user_with_profile(client):
    r = client.post("/api/v1/auth/register", json={
        "email": "alice@example.com", "password": "supersecret1",
        "full_name": "Alice", "role": "instructor",
    })
    assert r.status_code == 201
    body = r.json()
    assert body["access_token"]
    assert body["user"]["email"] == "alice@example.com"
    assert body["user"]["role"] == "instructor"
    assert body["user"]["profile"] is not None  # 1:1 auto-created


def test_register_duplicate_email_409(client, instructor_token):
    r = client.post("/api/v1/auth/register", json={
        "email": "instructor@test.com", "password": "supersecret1",
        "full_name": "X", "role": "student",
    })
    assert r.status_code == 409


def test_login_success_returns_jwt(client, student_token):
    r = client.post("/api/v1/auth/login", json={
        "email": "student@test.com", "password": "supersecret1",
    })
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password_401(client, student_token):
    r = client.post("/api/v1/auth/login", json={
        "email": "student@test.com", "password": "wrongpass1",
    })
    assert r.status_code == 401


def test_register_short_password_422(client):
    r = client.post("/api/v1/auth/register", json={
        "email": "a@b.com", "password": "short", "full_name": "A", "role": "student",
    })
    assert r.status_code == 422
