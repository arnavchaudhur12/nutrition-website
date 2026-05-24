from functools import lru_cache
from pathlib import Path
from typing import Literal
import json

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            str(REPO_ROOT / ".env"),
            str(BACKEND_ROOT / ".env"),
            ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Lagads Nutrition API"
    environment: Literal["local", "dev", "stage", "prod"] = "local"
    secret_key: str = Field(default="change-me-before-production", min_length=16)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    database_url: str = "sqlite:///./lagads_nutrition.db"
    cors_origins: list[str] = ["http://localhost:5173"]

    admin_email: str = "jai.lagad@lagadsnutrition.in"
    admin_password: str = "Xuv1997$"

    smtp_host: str = "smtp.office365.com"
    smtp_port: int = 587
    smtp_use_tls: bool = True
    smtp_user: str = "customercare@lagadsnutrition.in"
    smtp_password: str = ""
    smtp_sender_name: str = "Lagads Nutrition"
    notification_email: str = "jai.lagad@lagadsnutrition.in"

    payment_provider: str = "razorpay"
    payment_key_id: str = ""
    payment_key_secret: str = ""
    payment_webhook_secret: str = ""
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
