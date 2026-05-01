"""Shared pytest fixtures.

We override the database with an in-memory SQLite for fast, isolated tests.
"""
from __future__ import annotations

import warnings
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

warnings.filterwarnings("ignore")


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """Fresh TestClient with a fresh in-memory SQLite per test."""
    import app.core.database as db_mod

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    db_mod.engine = engine
    db_mod.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_mod.wait_for_db = lambda *a, **kw: None

    # Re-import main so its on_startup picks up the patched engine
    import importlib
    import app.main
    importlib.reload(app.main)

    with TestClient(app.main.app) as c:
        yield c


def _register(client: TestClient, email: str, role: str) -> str:
    r = client.post("/api/v1/auth/register", json={
        "email": email, "password": "supersecret1",
        "full_name": email.split("@")[0].title(), "role": role,
    })
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


@pytest.fixture
def instructor_token(client: TestClient) -> str:
    return _register(client, "instructor@test.com", "instructor")


@pytest.fixture
def student_token(client: TestClient) -> str:
    return _register(client, "student@test.com", "student")
