from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic import model_validator
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

    genzlogix_api_key: str = ""
    genzlogix_base_url: str = "https://genzlogix.com/api/v1/public"
    genzlogix_pickup_pincode: str = ""
    genzlogix_default_length_cm: float = 20
    genzlogix_default_breadth_cm: float = 15
    genzlogix_default_height_cm: float = 10

    google_sheet_id: str = ""
    google_sheet_worksheet: str = ""
    google_service_account_file: str = ""
    order_number_start: int = 13

    @model_validator(mode="after")
    def normalize_sqlite_database_url(self) -> "Settings":
        sqlite_prefix = "sqlite:///"
        if self.database_url.startswith(sqlite_prefix):
            raw_path = self.database_url[len(sqlite_prefix):]
            if raw_path.startswith("/"):
                return self
            normalized_path = (BACKEND_ROOT / raw_path).resolve()
            self.database_url = f"{sqlite_prefix}{normalized_path}"
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
