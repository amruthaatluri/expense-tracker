from datetime import date
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field, EmailStr


class BudgetCreate(BaseModel):
    month: str                 # "YYYY-MM"
    limit_amount: float
    category_id: Optional[int] = None  # null => overall budget

class BudgetOut(BudgetCreate):
    id: int
    user_id: int
    model_config = ConfigDict(from_attributes=True)

# ---------- Transaction ----------
class TransactionCreate(BaseModel):
    amount: float = Field(gt=0, description="Must be > 0")
    currency: str = "USD"  # keep simple for now; can restrict later
    note: Optional[str] = None
    tx_date: date
    category_id: int

class TransactionOut(BaseModel):
    id: int
    amount: float
    currency: str
    note: Optional[str]
    tx_date: date
    user_id: int
    category_id: int
    model_config = ConfigDict(from_attributes=True)


class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    currency: Optional[str] = None
    note: Optional[str] = None
    tx_date: Optional[date] = None
    category_id: Optional[int] = None

class CategoryCreate(BaseModel):
    name: str
    type: Literal["expense", "income"]  # only these two, enforced by Pydantic

class CategoryOut(CategoryCreate):
    id: int
    user_id: int
    model_config = ConfigDict(from_attributes=True)

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[Literal["expense", "income"]] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)
# ---- Auth Schemas ----

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
