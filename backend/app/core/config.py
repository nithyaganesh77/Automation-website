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

    # Database (PostgreSQL with SQLite fallback)
    DATABASE_URL: str = Field(
        default="sqlite:///./documind.db",
        validation_alias="DATABASE_URL"
    )

    # Redis / Celery
    REDIS_URL: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    CELERY_BROKER_URL: Optional[str] = Field(default=None, validation_alias="CELERY_BROKER_URL")

    # Qdrant Vector DB (Open Source Free Tier)
    QDRANT_URL: str = Field(default="http://localhost:6333", validation_alias="QDRANT_URL")

    # Storage: MinIO (Local S3-compatible) & Local Storage
    STORAGE_TYPE: str = Field(default="local", validation_alias="STORAGE_TYPE")  # local or minio
    UPLOAD_DIR: str = Field(default="storage/uploads", validation_alias="UPLOAD_DIR")
    MINIO_ENDPOINT: str = Field(default="localhost:9000", validation_alias="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin", validation_alias="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = Field(default="minioadmin", validation_alias="MINIO_SECRET_KEY")
    MINIO_BUCKET: str = Field(default="documind-documents", validation_alias="MINIO_BUCKET")
    MINIO_SECURE: bool = Field(default=False, validation_alias="MINIO_SECURE")

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

    # AI Free-First Architecture: Gemini (Primary) + Groq (Fallback)
    AI_PRIMARY_PROVIDER: str = Field(default="gemini", validation_alias="AI_PRIMARY_PROVIDER")
    AI_FALLBACK_PROVIDER: str = Field(default="groq", validation_alias="AI_FALLBACK_PROVIDER")
    GEMINI_API_KEY: Optional[str] = Field(default=None, validation_alias="GEMINI_API_KEY")
    GROQ_API_KEY: Optional[str] = Field(default=None, validation_alias="GROQ_API_KEY")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash", validation_alias="GEMINI_MODEL")
    GROQ_MODEL: str = Field(default="openai/gpt-oss-120b", validation_alias="GROQ_MODEL")

    # Document Privacy & Cost Protection
    DISABLE_EXTERNAL_AI: bool = Field(default=False, validation_alias="DISABLE_EXTERNAL_AI")
    DAILY_REQUEST_LIMIT: int = Field(default=1500, validation_alias="DAILY_REQUEST_LIMIT")
    MONTHLY_TOKEN_BUDGET: int = Field(default=1000000, validation_alias="MONTHLY_TOKEN_BUDGET")
    SAFE_QUOTA_MODE: bool = Field(default=True, validation_alias="SAFE_QUOTA_MODE")

    # Business Logic Defaults
    CONFIDENCE_THRESHOLD: float = 0.85
    AUTO_APPROVE_THRESHOLD: float = 0.98
    TAX_TOLERANCE_AMOUNT: float = 2.0  # ₹2.00 tolerance
    DEFAULT_CURRENCY: str = "INR"

    # Commercial Billing & Webhooks (Sandbox/Disabled by default)
    RAZORPAY_WEBHOOK_SECRET: str = Field(default="documind_test_webhook_secret_hmac_2026", validation_alias="RAZORPAY_WEBHOOK_SECRET")
    ENABLE_LIVE_PAYMENTS: bool = Field(default=False, validation_alias="ENABLE_LIVE_PAYMENTS")

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

# Ensure local upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
