import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "DocuMind AI"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = Field(default="development", validation_alias="ENVIRONMENT")
    DEBUG: bool = True

    # Security & Auth
    SECRET_KEY: str = Field(default="documind_ai_super_secret_jwt_key_enterprise_2026_change_in_production", validation_alias="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./documind.db",
        validation_alias="DATABASE_URL"
    )

    # Redis / Celery
    REDIS_URL: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    CELERY_BROKER_URL: Optional[str] = Field(default=None, validation_alias="CELERY_BROKER_URL")

    # Storage
    STORAGE_TYPE: str = Field(default="local", validation_alias="STORAGE_TYPE")  # local or s3
    UPLOAD_DIR: str = Field(default="storage/uploads", validation_alias="UPLOAD_DIR")
    MAX_FILE_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB
    ALLOWED_EXTENSIONS: List[str] = [
        "pdf", "png", "jpg", "jpeg", "docx", "xlsx"
    ]
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ]

    # AI Configuration
    AI_PROVIDER: str = Field(default="gemini", validation_alias="AI_PROVIDER")  # gemini, openai, local_synthetic
    GEMINI_API_KEY: Optional[str] = Field(default=None, validation_alias="GEMINI_API_KEY")
    OPENAI_API_KEY: Optional[str] = Field(default=None, validation_alias="OPENAI_API_KEY")
    GEMINI_MODEL: str = "gemini-2.0-flash"
    OPENAI_MODEL: str = "gpt-4o"

    # Business Logic Defaults
    CONFIDENCE_THRESHOLD: float = 0.85
    AUTO_APPROVE_THRESHOLD: float = 0.98
    TAX_TOLERANCE_AMOUNT: float = 2.0  # ₹2.00 tolerance for rounding differences
    DEFAULT_CURRENCY: str = "INR"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
