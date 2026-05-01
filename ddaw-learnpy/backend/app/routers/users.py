"""User and Profile endpoints — demonstrates the 1:1 relation in the API."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import Profile, User
from app.schemas.user import ProfileUpdate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserRead,
    summary="Current user (with their profile, 1:1 relation)",
)
def read_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.put(
    "/me/profile",
    response_model=UserRead,
    summary="Update the connected user's profile (1:1)",
)
def update_my_profile(
    payload: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    if current_user.profile is None:
        # Defensive: register() always creates a profile, but stay safe.
        current_user.profile = Profile()
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(current_user.profile, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user
