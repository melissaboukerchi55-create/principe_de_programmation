"""Pydantic schemas for Lesson."""
from pydantic import BaseModel, ConfigDict, Field


class LessonBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = ""
    position: int = Field(default=0, ge=0)
    duration_min: int = Field(default=0, ge=0)


class LessonCreate(LessonBase):
    pass


class LessonUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = None
    position: int | None = Field(default=None, ge=0)
    duration_min: int | None = Field(default=None, ge=0)


class LessonRead(LessonBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    course_id: int
