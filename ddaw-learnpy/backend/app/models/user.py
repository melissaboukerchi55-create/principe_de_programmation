"""User and Profile models — demonstrates the One-to-One relationship."""
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, Enum):
    STUDENT = "student"
    INSTRUCTOR = "instructor"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=UserRole.STUDENT.value)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ----- Relation 1:1 with Profile ----- #
    # uselist=False on the parent side + unique FK on the child side = strict 1:1
    profile: Mapped["Profile | None"] = relationship(
        "Profile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # ----- Relation 1:N (as instructor) with Course ----- #
    courses_taught: Mapped[list["Course"]] = relationship(
        "Course",
        back_populates="instructor",
        cascade="all, delete-orphan",
        foreign_keys="Course.instructor_id",
    )

    # ----- Relation N:M (as student) with Course via Enrollment ----- #
    enrollments: Mapped[list["Enrollment"]] = relationship(
        "Enrollment",
        back_populates="student",
        cascade="all, delete-orphan",
        foreign_keys="Enrollment.student_id",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} email={self.email} role={self.role}>"


class Profile(Base):
    """Extended user profile — exists at most once per user (1:1)."""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    # UNIQUE constraint on the FK enforces 1:1 at the database level
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    bio: Mapped[str | None] = mapped_column(String(1000))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    github_url: Mapped[str | None] = mapped_column(String(500))

    user: Mapped["User"] = relationship("User", back_populates="profile")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Profile id={self.id} user_id={self.user_id}>"
