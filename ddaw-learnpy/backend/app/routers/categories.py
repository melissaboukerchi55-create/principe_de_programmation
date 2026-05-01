"""Category endpoints — parent of the 1:N relation with Course."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead], summary="List all categories")
def list_categories(db: Annotated[Session, Depends(get_db)]):
    return db.scalars(select(Category).order_by(Category.name)).all()


@router.get("/{category_id}", response_model=CategoryRead, summary="Get one category")
def get_category(category_id: int, db: Annotated[Session, Depends(get_db)]):
    cat = db.get(Category, category_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a category (instructor only)",
    dependencies=[Depends(require_role("instructor"))],
)
def create_category(payload: CategoryCreate, db: Annotated[Session, Depends(get_db)]):
    cat = Category(**payload.model_dump())
    db.add(cat)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Name or slug already exists")
    db.refresh(cat)
    return cat


@router.put(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Update a category (instructor only)",
    dependencies=[Depends(require_role("instructor"))],
)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    cat = db.get(Category, category_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="Category not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cat, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Name or slug already exists")
    db.refresh(cat)
    return cat


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category (instructor only)",
    dependencies=[Depends(require_role("instructor"))],
)
def delete_category(category_id: int, db: Annotated[Session, Depends(get_db)]):
    cat = db.get(Category, category_id)
    if cat is None:
        raise HTTPException(status_code=404, detail="Category not found")
    if cat.courses:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete category with associated courses",
        )
    db.delete(cat)
    db.commit()
