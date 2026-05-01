"""Enrollment model — Many-to-Many association class between Student (User) and Course.

Implemented as a real ORM class (not a plain association table) because we need extra
columns: enrolled_at, progress, rating. This is the proper way to represent a M:N
relationship with attributes in SQLAlchemy.
"""
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        CheckConstraint("progress >= 0 AND progress <= 100", name="ck_progress_range"),
        CheckConstraint(
            "rating IS NULL OR (rating >= 1 AND rating <= 5)", name="ck_rating_range"
        ),
    )

    # Composite primary key (student_id, course_id) — ensures one enrollment per pair
    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True
    )

    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating: Mapped[int | None] = mapped_column(Integer)

    # ----- Both sides of the M:N relationship ----- #
    student: Mapped["User"] = relationship(
        "User", back_populates="enrollments", foreign_keys=[student_id]
    )
    course: Mapped["Course"] = relationship("Course", back_populates="enrollments")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Enrollment student_id={self.student_id} course_id={self.course_id}>"
