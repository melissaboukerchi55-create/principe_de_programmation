"""Authentication endpoints: register and login."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import Profile, User
from app.schemas.user import LoginRequest, TokenResponse, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new account (student or instructor)",
)
def register(
    payload: UserCreate,
    db: Annotated[Session, Depends(get_db)],
):
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        role=payload.role.value,
        hashed_password=hash_password(payload.password),
    )
    # Auto-create empty profile (1:1) — keeps the relation consistent from day one
    user.profile = Profile()
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    db.refresh(user)
    token = create_access_token(user.id, extra={"role": user.role})
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive a JWT",
)
def login(
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(user.id, extra={"role": user.role})
    return TokenResponse(access_token=token, user=UserRead.model_validate(user))
