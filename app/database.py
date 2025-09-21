from typing import Generator
from app.db.session import SessionLocal
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db   # hand a fresh session to the route
    finally:
        db.close() 