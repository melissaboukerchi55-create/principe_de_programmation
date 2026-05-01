"""Pydantic schemas for Enrollment (N:M association)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.course import CourseRead


class EnrollmentUpdate(BaseModel):
    """Update progress and/or rating on an existing enrollment."""
    progress: int | None = Field(default=None, ge=0, le=100)
    rating: int | None = Field(default=None, ge=1, le=5)


class EnrollmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    student_id: int
    course_id: int
    enrolled_at: datetime
    progress: int
    rating: int | None = None


class EnrollmentDetail(EnrollmentRead):
    """Full enrollment with embedded course info (for /users/me/enrollments)."""
    course: CourseRead


class StudentInCourse(BaseModel):
    """Student listing with their enrollment state, for instructor view."""
    model_config = ConfigDict(from_attributes=True)
    student_id: int
    student_email: str
    student_name: str
    enrolled_at: datetime
    progress: int
    rating: int | None
