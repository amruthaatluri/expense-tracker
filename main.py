from fastapi import FastAPI
from app.db.session import Base, engine
from app.routes.transactions import router as transactions_router
from app.routes.categories import router as categories_router
from app.routes.users import router as users_router
from app.routes.auth import router as auth_router
from app.routes.reports import router as reports_router
from app.routes.budgets import router as budgets_router
from fastapi.middleware.cors import CORSMiddleware
from app.core.settings import settings
import app.models
app=FastAPI()
@app.get("/")
def home():
    return{"message": "Expense tracker is runnning"}
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
app.include_router(transactions_router)
app.include_router(categories_router)
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(reports_router)
app.include_router(budgets_router)
origins = settings.allowed_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)