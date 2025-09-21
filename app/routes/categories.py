from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.core.deps import get_current_user

router = APIRouter(prefix="/categories", tags=["categories"])

@router.post("/", response_model=schemas.CategoryOut, status_code=201)
def create_category(
    payload: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # prevent duplicate category name+type for this user
    existing = (
        db.query(models.Category)
        .filter(
            models.Category.user_id == current_user.id,
            models.Category.name == payload.name,
            models.Category.type == payload.type,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")

    cat = models.Category(
        name=payload.name,
        type=payload.type,
        user_id=current_user.id,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.get("/", response_model=List[schemas.CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return (
        db.query(models.Category)
        .filter(models.Category.user_id == current_user.id)
        .order_by(models.Category.id)
        .offset(offset)
        .limit(limit)
        .all()
    )
from fastapi import Path

@router.patch("/{category_id}", response_model=schemas.CategoryOut)
def update_category(
    category_id: int = Path(..., gt=0),
    payload: schemas.CategoryUpdate = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    cat = (
        db.query(models.Category)
        .filter(
            models.Category.id == category_id,
            models.Category.user_id == current_user.id,
        )
        .first()
    )
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    data = payload.model_dump(exclude_unset=True)

    # prevent duplicate (name,type) for this user if either changed
    if "name" in data or "type" in data:
        name = data.get("name", cat.name)
        ctype = data.get("type", cat.type)
        exists = (
            db.query(models.Category)
            .filter(
                models.Category.user_id == current_user.id,
                models.Category.name == name,
                models.Category.type == ctype,
                models.Category.id != cat.id,
            )
            .first()
        )
        if exists:
            raise HTTPException(status_code=400, detail="Category already exists")

    for k, v in data.items():
        setattr(cat, k, v)

    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    cat = (
        db.query(models.Category)
        .filter(
            models.Category.id == category_id,
            models.Category.user_id == current_user.id,
        )
        .first()
    )
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(cat)
    db.commit()
