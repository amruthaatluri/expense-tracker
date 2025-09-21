# app/routes/budgets.py
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.core.deps import get_current_user
from app import models, schemas

router = APIRouter(prefix="/budgets", tags=["budgets"])

@router.post("/", response_model=schemas.BudgetOut, status_code=201)
def create_budget(
    payload: schemas.BudgetCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # if category_id provided, ensure it belongs to user
    if payload.category_id is not None:
        cat = (
            db.query(models.Category)
            .filter(
                models.Category.id == payload.category_id,
                models.Category.user_id == current_user.id,
            ).first()
        )
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found for this user")

    # upsert-like: prevent duplicate for (user, month, category_id)
    existing = (
        db.query(models.Budget)
        .filter(
            models.Budget.user_id == current_user.id,
            models.Budget.month == payload.month,
            models.Budget.category_id == payload.category_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Budget already exists for this scope")

    b = models.Budget(
        user_id=current_user.id,
        month=payload.month,
        category_id=payload.category_id,
        limit_amount=payload.limit_amount,
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return b

@router.get("/", response_model=List[schemas.BudgetOut])
def list_budgets(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    month: Optional[str] = Query(None, description='Filter by "YYYY-MM"'),
):
    q = db.query(models.Budget).filter(models.Budget.user_id == current_user.id)
    if month:
        q = q.filter(models.Budget.month == month)
    return q.order_by(models.Budget.month.desc(), models.Budget.id.desc()).all()

@router.patch("/{budget_id}", response_model=schemas.BudgetOut)
def update_budget(
    budget_id: int = Path(..., gt=0),
    payload: schemas.BudgetCreate = None,  # reuse fields; all optional would be nicer with a BudgetUpdate
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    b = (
        db.query(models.Budget)
        .filter(models.Budget.id == budget_id, models.Budget.user_id == current_user.id)
        .first()
    )
    if not b:
        raise HTTPException(status_code=404, detail="Budget not found")

    data = payload.model_dump(exclude_unset=True)
    # prevent changing to an existing (user, month, category_id) combo
    new_month = data.get("month", b.month)
    new_cat = data.get("category_id", b.category_id)
    dup = (
        db.query(models.Budget)
        .filter(
            models.Budget.user_id == current_user.id,
            models.Budget.month == new_month,
            models.Budget.category_id == new_cat,
            models.Budget.id != b.id,
        ).first()
    )
    if dup:
        raise HTTPException(status_code=400, detail="Budget already exists for this scope")

    for k, v in data.items():
        setattr(b, k, v)

    db.commit()
    db.refresh(b)
    return b

@router.delete("/{budget_id}", status_code=204)
def delete_budget(
    budget_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    b = (
        db.query(models.Budget)
        .filter(models.Budget.id == budget_id, models.Budget.user_id == current_user.id)
        .first()
    )
    if not b:
        raise HTTPException(status_code=404, detail="Budget not found")

    db.delete(b)
    db.commit()

@router.get("/progress")
def budget_progress(
    month: str = Query(..., description='"YYYY-MM"'),
    category_id: Optional[int] = Query(None, description="If omitted, computes overall"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> Dict[str, Any]:
    # find matching budget
    budget = (
        db.query(models.Budget)
        .filter(
            models.Budget.user_id == current_user.id,
            models.Budget.month == month,
            models.Budget.category_id == category_id,
        ).first()
    )
    if not budget:
        raise HTTPException(status_code=404, detail="No budget set for this scope")

    # figure month boundaries
    # naive boundaries using string prefix match on "YYYY-MM"
    # Sum only EXPENSE transactions for this user in that month (+ optional category)
    q = (
        db.query(func.coalesce(func.sum(models.Transaction.amount), 0))
        .select_from(models.Transaction)
        .join(models.Category, models.Category.id == models.Transaction.category_id)
        .filter(
            models.Transaction.user_id == current_user.id,
            models.Category.type == "expense",
            func.strftime("%Y-%m", models.Transaction.tx_date) == month,
        )
    )
    if category_id is not None:
        q = q.filter(models.Transaction.category_id == category_id)

    spent = float(q.scalar())
    limit_amount = float(budget.limit_amount)
    remaining = float(max(limit_amount - spent, 0.0))
    used_pct = float(0 if limit_amount == 0 else (spent / limit_amount) * 100.0)

    return {
        "month": month,
        "scope": "category" if category_id is not None else "overall",
        "category_id": category_id,
        "limit": limit_amount,
        "spent": spent,
        "remaining": remaining,
        "used_percent": round(used_pct, 2),
    }
