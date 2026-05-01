"""Lesson endpoints — child of the 1:N relation with Course."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.models.course import Course, Lesson
from app.models.user import User
from app.schemas.lesson import LessonCreate, LessonRead, LessonUpdate

router = APIRouter(tags=["lessons"])


def _get_course_owned(db: Session, course_id: int, user: User) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.instructor_id != user.id:
        raise HTTPException(status_code=403, detail="You are not the owner of this course")
    return course


@router.get(
    "/courses/{course_id}/lessons",
    response_model=list[LessonRead],
    summary="List lessons of a course (ordered by position)",
)
def list_lessons(course_id: int, db: Annotated[Session, Depends(get_db)]):
    if db.get(Course, course_id) is None:
        raise HTTPException(status_code=404, detail="Course not found")
    stmt = select(Lesson).where(Lesson.course_id == course_id).order_by(Lesson.position)
    return db.scalars(stmt).all()


@router.post(
    "/courses/{course_id}/lessons",
    response_model=LessonRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a lesson (owner only)",
)
def create_lesson(
    course_id: int,
    payload: LessonCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("instructor"))],
):
    _get_course_owned(db, course_id, current_user)
    lesson = Lesson(**payload.model_dump(), course_id=course_id)
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


@router.put(
    "/lessons/{lesson_id}",
    response_model=LessonRead,
    summary="Update a lesson (owner of parent course only)",
)
def update_lesson(
    lesson_id: int,
    payload: LessonUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("instructor"))],
):
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    _get_course_owned(db, lesson.course_id, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lesson, field, value)
    db.commit()
    db.refresh(lesson)
    return lesson


@router.delete(
    "/lessons/{lesson_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a lesson (owner only)",
)
def delete_lesson(
    lesson_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("instructor"))],
):
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    _get_course_owned(db, lesson.course_id, current_user)
    db.delete(lesson)
    db.commit()
