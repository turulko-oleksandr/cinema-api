import os
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings


class BaseAppSettings(BaseSettings):
    BASE_DIR: Path = Path(__file__).parent.parent
    PATH_TO_DB: str = str(BASE_DIR / "database" / "source" / "cinema.db")
    LOGIN_TIME_DAYS: int = 7
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SYNC_PGSQL_DB_LINK: str = os.environ.get("PGSQL_SYNC_URL")
    ASYNC_PGSQL_URL: str = os.environ.get("PGSQL_URL")


class Settings(BaseAppSettings):
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "test_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "test_password")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "test_host")
    POSTGRES_DB_PORT: int = int(os.getenv("POSTGRES_DB_PORT", 5432))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "test_db")

    SECRET_KEY_ACCESS: str = os.getenv("SECRET_KEY_ACCESS", os.urandom(32))
    SECRET_KEY_REFRESH: str = os.getenv("SECRET_KEY_REFRESH", os.urandom(32))
    JWT_SIGNING_ALGORITHM: str = os.getenv("JWT_SIGNING_ALGORITHM", "HS256")

    # Email
    EMAIL_HOST: str = os.getenv("EMAIL_HOST", "localhost")
    EMAIL_PORT: int = int(os.getenv("EMAIL_PORT", "8025"))
    EMAIL_HOST_USER: str = os.getenv("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD: str = os.getenv("EMAIL_HOST_PASSWORD", "")
    EMAIL_USE_TLS: bool = os.getenv("EMAIL_USE_TLS", "False").lower() == "true"
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@cinema.com")
    EMAIL_FROM_NAME: str = os.getenv("EMAIL_FROM_NAME", "Cinema App")

    # Frontend URLs
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    ACTIVATION_URL: str = f"{FRONTEND_URL}/activate"
    PASSWORD_RESET_URL: str = f"{FRONTEND_URL}/reset-password"

    # Celery
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
    )

    # Stripe
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_SUCCESS_URL: str = os.getenv(
        "STRIPE_SUCCESS_URL", f"{FRONTEND_URL}/payment/success"
    )
    STRIPE_CANCEL_URL: str = os.getenv(
        "STRIPE_CANCEL_URL", f"{FRONTEND_URL}/payment/cancel"
    )

    # MinIO
    MINIO_HOST: str = os.getenv("MINIO_HOST", "localhost")
    MINIO_PORT: int = int(os.getenv("MINIO_PORT", "9000"))
    MINIO_ROOT_USER: str = os.getenv("MINIO_ROOT_USER", "minioadmin")
    MINIO_ROOT_PASSWORD: str = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
    MINIO_STORAGE: str = os.getenv("MINIO_STORAGE", "cinema-storage")


class TestingSettings(BaseAppSettings):
    SECRET_KEY_ACCESS: str = "SECRET_KEY_ACCESS"
    SECRET_KEY_REFRESH: str = "SECRET_KEY_REFRESH"
    JWT_SIGNING_ALGORITHM: str = "HS256"

    # Email
    EMAIL_HOST: str = os.getenv("EMAIL_HOST", "localhost")
    EMAIL_PORT: int = int(os.getenv("EMAIL_PORT", "1025"))
    EMAIL_HOST_USER: str = os.getenv("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD: str = os.getenv("EMAIL_HOST_PASSWORD", "")
    EMAIL_USE_TLS: bool = os.getenv("EMAIL_USE_TLS", "False").lower() == "true"
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@cinema.com")
    EMAIL_FROM_NAME: str = os.getenv("EMAIL_FROM_NAME", "Cinema App")

    # Frontend URLs
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    ACTIVATION_URL: str = f"{FRONTEND_URL}/activate"
    PASSWORD_RESET_URL: str = f"{FRONTEND_URL}/reset-password"

    # Celery
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
    )

    # Stripe
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_SUCCESS_URL: str = os.getenv(
        "STRIPE_SUCCESS_URL", f"{FRONTEND_URL}/payment/success"
    )
    STRIPE_CANCEL_URL: str = os.getenv(
        "STRIPE_CANCEL_URL", f"{FRONTEND_URL}/payment/cancel"
    )

    # MinIO
    MINIO_HOST: str = os.getenv("MINIO_HOST", "localhost")
    MINIO_PORT: int = int(os.getenv("MINIO_PORT", "9000"))
    MINIO_ROOT_USER: str = os.getenv("MINIO_ROOT_USER", "minioadmin")
    MINIO_ROOT_PASSWORD: str = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
    MINIO_STORAGE: str = os.getenv("MINIO_STORAGE", "test-storage")

    def model_post_init(self, __context: dict[str, Any] | None = None) -> None:
        object.__setattr__(self, "PATH_TO_DB", ":memory:")
        object.__setattr__(
            self,
            "PATH_TO_MOVIES_CSV",
            str(self.BASE_DIR / "database" / "seed_data" / "test_data.csv"),
        )