from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.database import get_db
from app import models, schemas
from app.core.deps import get_current_user
router = APIRouter(prefix="/transactions", tags=["transactions"])
@router.post("/", response_model=schemas.TransactionOut, status_code=201)
def create_transaction(
    payload: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),   # require login
):
    # make sure category exists and belongs to this user
    category = (
        db.query(models.Category)
        .filter(
            models.Category.id == payload.category_id,
            models.Category.user_id == current_user.id,
        )
        .first()
    )
    if not category:
        raise HTTPException(status_code=404, detail="Category not found for this user")

    # ignore any user_id in payload; use the token’s user
    tx = models.Transaction(
        amount=payload.amount,
        currency=payload.currency,
        note=payload.note,
        tx_date=payload.tx_date,
        user_id=current_user.id,
        category_id=payload.category_id,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx
from fastapi import Path

@router.patch("/{tx_id}", response_model=schemas.TransactionOut)
def update_transaction(
    tx_id: int = Path(..., gt=0),
    payload: schemas.TransactionUpdate = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    tx = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.id == tx_id,
            models.Transaction.user_id == current_user.id,
        )
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    data = payload.model_dump(exclude_unset=True)

    # if category change requested, validate it belongs to the user
    if "category_id" in data and data["category_id"] is not None:
        cat = (
            db.query(models.Category)
            .filter(
                models.Category.id == data["category_id"],
                models.Category.user_id == current_user.id,
            )
            .first()
        )
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found for this user")

    for k, v in data.items():
        setattr(tx, k, v)

    db.commit()
    db.refresh(tx)
    return tx


@router.delete("/{tx_id}", status_code=204)
def delete_transaction(
    tx_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    tx = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.id == tx_id,
            models.Transaction.user_id == current_user.id,
        )
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(tx)
    db.commit()


@router.get("/", response_model=List[schemas.TransactionOut])
def list_transactions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    category_id: Optional[int] = None,
    start_date: Optional[date] = Query(None, description="Inclusive, e.g. 2025-09-01"),
    end_date: Optional[date] = Query(None, description="Inclusive, e.g. 2025-09-30"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    q = db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id)

    if category_id is not None:
        q = q.filter(models.Transaction.category_id == category_id)
    if start_date is not None:
        q = q.filter(models.Transaction.tx_date >= start_date)
    if end_date is not None:
        q = q.filter(models.Transaction.tx_date <= end_date)

    return (
        q.order_by(models.Transaction.tx_date.desc(), models.Transaction.id.desc())
         .offset(offset)
         .limit(limit)
         .all()
    )