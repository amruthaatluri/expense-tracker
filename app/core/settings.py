# app/core/settings.py
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve project root: expense-tracker/
BASE_DIR = Path(__file__).resolve().parents[2]

# Load .env explicitly from project root
load_dotenv(BASE_DIR / ".env")

class Settings(BaseSettings):
    # Defaults so app boots even if .env is missing
    secret_key: str = "dev-secret-change-me"
    database_url: str = "sqlite:///./expense.db"
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Also tell pydantic-settings where the .env is
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
    )

settings = Settings()
