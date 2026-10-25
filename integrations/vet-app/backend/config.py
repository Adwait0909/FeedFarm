from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    DATABASE_URL: str = f"sqlite+aiosqlite:///{(BACKEND_DIR / 'veterinary.sqlite3').as_posix()}"
    SYNC_DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/vet_assist"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    KML_DATA_DIR: str = str(BACKEND_DIR / "data")

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
