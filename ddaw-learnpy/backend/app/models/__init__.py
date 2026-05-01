"""Re-export all ORM models so Base.metadata.create_all picks them up."""
from app.models.category import Category
from app.models.course import Course, Lesson
from app.models.enrollment import Enrollment
from app.models.user import Profile, User, UserRole

__all__ = [
    "Category",
    "Course",
    "Lesson",
    "Enrollment",
    "Profile",
    "User",
    "UserRole",
]
