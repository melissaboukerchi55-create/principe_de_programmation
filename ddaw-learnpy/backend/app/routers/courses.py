"""Course endpoints — covers GET/POST/PUT/PATCH/DELETE."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.category import Category
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.user import User
from app.schemas.course import CourseCreate, CourseDetail, CourseRead, CourseUpdate
from app.schemas.enrollment import StudentInCourse

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=list[CourseRead], summary="List courses (filterable)")
def list_courses(
    db: Annotated[Session, Depends(get_db)],
    category_id: int | None = Query(default=None),
    instructor_id: int | None = Query(default=None),
    published_only: bool = Query(default=False),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
):
    stmt = (
        select(Course)
        .options(selectinload(Course.category), selectinload(Course.instructor))
        .order_by(Course.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    if category_id is not None:
        stmt = stmt.where(Course.category_id == category_id)
    if instructor_id is not None:
        stmt = stmt.where(Course.instructor_id == instructor_id)
    if published_only:
        stmt = stmt.where(Course.published.is_(True))
    return db.scalars(stmt).all()


@router.get(
    "/{course_id}",
    response_model=CourseDetail,
    summary="Course detail with lessons (1:N relation)",
)
def get_course(course_id: int, db: Annotated[Session, Depends(get_db)]):
    stmt = (
        select(Course)
        .options(
            selectinload(Course.lessons),
            selectinload(Course.category),
            selectinload(Course.instructor),
        )
        .where(Course.id == course_id)
    )
    course = db.scalar(stmt)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.post(
    "",
    response_model=CourseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a course (instructor only)",
)
def create_course(
    payload: CourseCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("instructor"))],
):
    if db.get(Category, payload.category_id) is None:
        raise HTTPException(status_code=404, detail="Category not found")
    course = Course(**payload.model_dump(), instructor_id=current_user.id)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def _ensure_owner(course: Course, current_user: User) -> None:
    if course.instructor_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not the owner of this course")


@router.put(
    "/{course_id}",
    response_model=CourseRead,
    summary="Replace a course (owner only)",
)
def update_course(
    course_id: int,
    payload: CourseCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("instructor"))],
):
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    _ensure_owner(course, current_user)
    if db.get(Category, payload.category_id) is None:
        raise HTTPException(status_code=404, detail="Category not found")
    for field, value in payload.model_dump().items():
        setattr(course, field, value)
    db.commit()
    db.refresh(course)
    return course


@router.patch(
    "/{course_id}",
    response_model=CourseRead,
    summary="Partial update (owner only) — useful to publish/unpublish",
)
def patch_course(
    course_id: int,
    payload: CourseUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("instructor"))],
):
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    _ensure_owner(course, current_user)
    data = payload.model_dump(exclude_unset=True)
    if "category_id" in data and db.get(Category, data["category_id"]) is None:
        raise HTTPException(status_code=404, detail="Category not found")
    for field, value in data.items():
        setattr(course, field, value)
    db.commit()
    db.refresh(course)
    return course


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a course (owner only) — cascades to lessons and enrollments",
)
def delete_course(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("instructor"))],
):
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    _ensure_owner(course, current_user)
    db.delete(course)
    db.commit()


@router.get(
    "/{course_id}/students",
    response_model=list[StudentInCourse],
    summary="List enrolled students (owner only) — exposes the N:M attributes",
)
def list_course_students(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("instructor"))],
):
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    _ensure_owner(course, current_user)

    stmt = (
        select(Enrollment)
        .options(selectinload(Enrollment.student))
        .where(Enrollment.course_id == course_id)
    )
    enrollments = db.scalars(stmt).all()
    return [
        StudentInCourse(
            student_id=e.student_id,
            student_email=e.student.email,
            student_name=e.student.full_name,
            enrolled_at=e.enrolled_at,
            progress=e.progress,
            rating=e.rating,
        )
        for e in enrollments
    ]
