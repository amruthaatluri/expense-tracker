from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Date, func
from sqlalchemy.orm import relationship
from app.db.session import Base
# app/models.py (append at bottom)
from sqlalchemy import UniqueConstraint

class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (
        # one budget per (user, month, category) — category_id can be NULL for "overall"
        UniqueConstraint("user_id", "month", "category_id", name="uq_budget_user_month_category"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # format: "YYYY-MM", e.g. "2025-09"
    month = Column(String, nullable=False)
    # optional: NULL means overall budget (not tied to a specific category)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    limit_amount = Column(Numeric(10, 2), nullable=False)

    user = relationship("User")         # no back_populates needed here
    category = relationship("Category") # optional

class User(Base):
    __tablename__= "users"
    id= Column(Integer, primary_key= True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'expense' or 'income'
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", backref="categories")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Numeric(10,2), nullable=False)
    currency = Column(String, default="USD")
    note = Column(String)
    tx_date = Column(Date, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    user = relationship("User", backref="transactions")
    category = relationship("Category", backref="transactions")
