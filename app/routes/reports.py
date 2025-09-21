from datetime import date
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user
from app import models

router = APIRouter(prefix="/reports", tags=["reports"])

def _apply_date_range(q, start_date: Optional[date], end_date: Optional[date]):
    if start_date is not None:
        q = q.filter(models.Transaction.tx_date >= start_date)
    if end_date is not None:
        q = q.filter(models.Transaction.tx_date <= end_date)
    return q

@router.get("/summary")
def summary_report(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    start_date: Optional[date] = Query(None, description="Inclusive yyyy-mm-dd"),
    end_date: Optional[date] = Query(None, description="Inclusive yyyy-mm-dd"),
) -> Dict[str, Any]:
    # Base filter: current user
    base = db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id)
    base = _apply_date_range(base, start_date, end_date)

    # Totals by type
    total_income = (
        db.query(func.coalesce(func.sum(models.Transaction.amount), 0))
        .select_from(models.Transaction)
        .join(models.Category, models.Category.id == models.Transaction.category_id)
        .filter(
            models.Transaction.user_id == current_user.id,
            models.Category.type == "income",
        )
    )
    total_income = _apply_date_range(total_income, start_date, end_date).scalar()

    total_expense = (
        db.query(func.coalesce(func.sum(models.Transaction.amount), 0))
        .select_from(models.Transaction)
        .join(models.Category, models.Category.id == models.Transaction.category_id)
        .filter(
            models.Transaction.user_id == current_user.id,
            models.Category.type == "expense",
        )
    )
    total_expense = _apply_date_range(total_expense, start_date, end_date).scalar()

    # Per-category totals
    per_cat_rows = (
        db.query(
            models.Category.id.label("category_id"),
            models.Category.name.label("name"),
            models.Category.type.label("type"),
            func.coalesce(func.sum(models.Transaction.amount), 0).label("total"),
        )
        .select_from(models.Transaction)
        .join(models.Category, models.Category.id == models.Transaction.category_id)
        .filter(models.Transaction.user_id == current_user.id)
        .group_by(models.Category.id, models.Category.name, models.Category.type)
    )
    per_cat_rows = _apply_date_range(per_cat_rows, start_date, end_date).all()

    by_category: List[Dict[str, Any]] = [
        {
            "category_id": r.category_id,
            "name": r.name,
            "type": r.type,
            "total": float(r.total),
        }
        for r in per_cat_rows
    ]

    return {
        "start_date": start_date,
        "end_date": end_date,
        "income": float(total_income),
        "expense": float(total_expense),
        "net": float(total_income - total_expense),
        "by_category": by_category,
    }
