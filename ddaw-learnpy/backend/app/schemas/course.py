"""Pydantic schemas for Course."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.category import CategoryRead
from app.schemas.lesson import LessonRead


class CourseBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    category_id: int
    published: bool = False


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    category_id: int | None = None
    published: bool | None = None


class CourseAuthor(BaseModel):
    """Light representation of the instructor inside a Course response."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    email: str


class CourseRead(BaseModel):
    """Course response without nested lessons (for list endpoints)."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str | None
    published: bool
    created_at: datetime
    category_id: int
    instructor_id: int
    instructor: CourseAuthor
    category: CategoryRead


class CourseDetail(CourseRead):
    """Course response with nested lessons (for detail endpoint)."""
    lessons: list[LessonRead] = Field(default_factory=list)
