from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
