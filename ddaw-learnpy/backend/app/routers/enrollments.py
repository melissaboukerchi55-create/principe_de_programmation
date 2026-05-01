"""Enrollment endpoints — Many-to-Many between Student and Course with attributes."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.user import User
from app.schemas.enrollment import EnrollmentDetail, EnrollmentRead, EnrollmentUpdate

router = APIRouter(tags=["enrollments"])


@router.post(
    "/courses/{course_id}/enroll",
    response_model=EnrollmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Enroll the connected student in a course",
)
def enroll(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("student"))],
):
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    existing = db.get(Enrollment, (current_user.id, course_id))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Already enrolled")

    enrollment = Enrollment(student_id=current_user.id, course_id=course_id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


@router.delete(
    "/courses/{course_id}/enroll",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unenroll the connected student",
)
def unenroll(
    course_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("student"))],
):
    enrollment = db.get(Enrollment, (current_user.id, course_id))
    if enrollment is None:
        raise HTTPException(status_code=404, detail="Not enrolled in this course")
    db.delete(enrollment)
    db.commit()


@router.patch(
    "/courses/{course_id}/enroll",
    response_model=EnrollmentRead,
    summary="Update progress and/or rating on the connected student's enrollment",
)
def update_enrollment(
    course_id: int,
    payload: EnrollmentUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("student"))],
):
    enrollment = db.get(Enrollment, (current_user.id, course_id))
    if enrollment is None:
        raise HTTPException(status_code=404, detail="Not enrolled in this course")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(enrollment, field, value)
    db.commit()
    db.refresh(enrollment)
    return enrollment


@router.get(
    "/users/me/enrollments",
    response_model=list[EnrollmentDetail],
    summary="Courses the connected student is enrolled in",
)
def my_enrollments(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    stmt = (
        select(Enrollment)
        .options(
            selectinload(Enrollment.course).selectinload(Course.category),
            selectinload(Enrollment.course).selectinload(Course.instructor),
        )
        .where(Enrollment.student_id == current_user.id)
        .order_by(Enrollment.enrolled_at.desc())
    )
    return db.scalars(stmt).all()
