"""Seed initial data — runs automatically on first launch if the DB is empty.

This is preferred over /docker-entrypoint-initdb.d/seed.sql for two reasons:
1. It runs *after* SQLAlchemy has created the schema from the ORM models, so we
   never duplicate DDL between the model layer and a SQL file.
2. It's idempotent — re-running the API on a populated DB is a no-op.

A separate db/seed.sql is also shipped for course evaluators who prefer raw SQL,
mirroring the same data.
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.category import Category
from app.models.course import Course, Lesson
from app.models.enrollment import Enrollment
from app.models.user import Profile, User, UserRole

logger = logging.getLogger(__name__)


SEED_PASSWORD = "demo1234"  # noqa: S105 — documented in README as demo password


def seed_if_empty(db: Session) -> None:
    """Load demo data unless any user already exists."""
    if db.scalar(select(User).limit(1)) is not None:
        logger.info("Seed skipped (database is not empty)")
        return

    logger.info("Seeding demo data...")

    # --- Categories (3 — matches the SAE topic) ---
    react = Category(name="React", slug="react",
                     description="Modern UI development with React")
    node = Category(name="Node.js", slug="nodejs",
                    description="Server-side JavaScript with Node.js")
    django = Category(name="Django", slug="django",
                      description="Python web framework — batteries included")
    db.add_all([react, node, django])
    db.flush()

    # --- Instructors (2) ---
    alice = User(
        email="alice@learnpy.dev",
        full_name="Alice Martin",
        role=UserRole.INSTRUCTOR.value,
        hashed_password=hash_password(SEED_PASSWORD),
        profile=Profile(bio="Senior React engineer.", github_url="https://github.com/alice"),
    )
    karim = User(
        email="karim@learnpy.dev",
        full_name="Karim Benali",
        role=UserRole.INSTRUCTOR.value,
        hashed_password=hash_password(SEED_PASSWORD),
        profile=Profile(bio="Backend specialist (Node + Django).",
                        github_url="https://github.com/karim"),
    )

    # --- Students (3) ---
    bob = User(
        email="bob@learnpy.dev",
        full_name="Bob Dupont",
        role=UserRole.STUDENT.value,
        hashed_password=hash_password(SEED_PASSWORD),
        profile=Profile(bio="CS student, eager to learn the modern web stack."),
    )
    chloe = User(
        email="chloe@learnpy.dev",
        full_name="Chloé Petit",
        role=UserRole.STUDENT.value,
        hashed_password=hash_password(SEED_PASSWORD),
        profile=Profile(bio="Junior dev pivoting from Java to Python."),
    )
    dimitri = User(
        email="dimitri@learnpy.dev",
        full_name="Dimitri Volkov",
        role=UserRole.STUDENT.value,
        hashed_password=hash_password(SEED_PASSWORD),
        profile=Profile(),
    )
    db.add_all([alice, karim, bob, chloe, dimitri])
    db.flush()

    # --- Courses (4) + Lessons ---
    react_basics = Course(
        title="React Basics",
        description="Foundations: components, JSX, state, hooks.",
        category_id=react.id,
        instructor_id=alice.id,
        published=True,
        lessons=[
            Lesson(title="Introduction to React", content="What is React, virtual DOM",
                   position=1, duration_min=20),
            Lesson(title="JSX & components", content="Composing your first components",
                   position=2, duration_min=35),
            Lesson(title="State and useState", content="Managing local state",
                   position=3, duration_min=40),
        ],
    )
    react_advanced = Course(
        title="Advanced React Patterns",
        description="Hooks, context, performance, code-splitting.",
        category_id=react.id,
        instructor_id=alice.id,
        published=True,
        lessons=[
            Lesson(title="Custom hooks", position=1, duration_min=45),
            Lesson(title="Context API", position=2, duration_min=30),
        ],
    )
    node_api = Course(
        title="Building REST APIs with Node.js",
        description="Express, async patterns, middlewares, testing.",
        category_id=node.id,
        instructor_id=karim.id,
        published=True,
        lessons=[
            Lesson(title="Setting up Express", position=1, duration_min=25),
            Lesson(title="Routing & middlewares", position=2, duration_min=35),
            Lesson(title="Persistence with an ORM", position=3, duration_min=50),
        ],
    )
    django_intro = Course(
        title="Django from Zero",
        description="Models, views, templates, admin, ORM.",
        category_id=django.id,
        instructor_id=karim.id,
        published=False,  # draft, not yet published
        lessons=[
            Lesson(title="Project layout", position=1, duration_min=20),
            Lesson(title="The ORM", position=2, duration_min=40),
        ],
    )
    db.add_all([react_basics, react_advanced, node_api, django_intro])
    db.flush()

    # --- Enrollments (M:N with attributes) ---
    db.add_all([
        Enrollment(student_id=bob.id, course_id=react_basics.id, progress=80, rating=5),
        Enrollment(student_id=bob.id, course_id=node_api.id, progress=30),
        Enrollment(student_id=chloe.id, course_id=django_intro.id, progress=50, rating=4),
        Enrollment(student_id=chloe.id, course_id=react_basics.id, progress=10),
        Enrollment(student_id=dimitri.id, course_id=react_advanced.id, progress=100, rating=5),
    ])

    db.commit()
    logger.info("Seed complete: 3 categories, 2 instructors, 3 students, 4 courses, 5 enrollments")
