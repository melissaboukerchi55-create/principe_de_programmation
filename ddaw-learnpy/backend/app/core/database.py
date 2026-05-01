"""Database setup: SQLAlchemy 2.0 engine, session factory, and FastAPI dependency."""
import logging
import time
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all ORM models."""


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # gracefully drop dead connections
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def wait_for_db(max_retries: int = 30, delay: float = 1.0) -> None:
    """Block until Postgres accepts connections (compose race condition safety net)."""
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            logger.info("Database is ready (attempt %d)", attempt)
            return
        except OperationalError as exc:
            logger.warning("DB not ready (attempt %d/%d): %s", attempt, max_retries, exc)
            time.sleep(delay)
    raise RuntimeError(f"Database not reachable after {max_retries} attempts")


def init_db() -> None:
    """Create all tables. For the SAE we use create_all instead of Alembic."""
    # Import all models so they are registered on Base.metadata
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("Tables created (or already existing)")
