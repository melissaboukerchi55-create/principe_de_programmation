"""Password hashing (bcrypt) and JWT token creation/validation.

Uses the `bcrypt` library directly rather than passlib, because passlib 1.7.4 has
a known compatibility issue with bcrypt >= 4.1 that breaks at import time.
Direct bcrypt is simpler, has fewer moving parts, and is the modern recommended
approach for FastAPI-style apps.
"""
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login")

# bcrypt's hard limit — passwords longer than 72 bytes are silently truncated.
# We enforce a clean length cap up front to make the behaviour explicit and safe.
_BCRYPT_MAX = 72


# ---------- Password helpers ---------- #
def hash_password(password: str) -> str:
    """Hash a password using bcrypt with a cost factor of 12."""
    pw_bytes = password.encode("utf-8")
    if len(pw_bytes) > _BCRYPT_MAX:
        raise ValueError("Password must be at most 72 bytes when encoded as UTF-8")
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time bcrypt verification."""
    pw_bytes = plain.encode("utf-8")
    if len(pw_bytes) > _BCRYPT_MAX:
        return False
    try:
        return bcrypt.checkpw(pw_bytes, hashed.encode("utf-8"))
    except ValueError:
        # Malformed hash → treat as failed verification
        return False


# ---------- JWT helpers ---------- #
def create_access_token(subject: str | int, extra: dict | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(subject), "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ---------- FastAPI dependencies ---------- #
def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
):
    """Resolve the JWT into a User instance."""
    from app.models.user import User  # local import avoids circular deps

    payload = decode_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.get(User, int(user_id))
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_role(*allowed_roles: str):
    """Dependency factory enforcing one of the given roles."""

    def _checker(current_user=Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not allowed (need: {', '.join(allowed_roles)})",
            )
        return current_user

    return _checker
