from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

API_ROOT = Path(__file__).resolve().parents[2]
_api_parents = API_ROOT.parents
REPO_ROOT = _api_parents[1] if len(_api_parents) > 1 else API_ROOT


class AppEnv(StrEnum):
    development = "development"
    staging = "staging"
    production = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", API_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    APP_NAME: str = "Zehno"
    APP_ENV: AppEnv = AppEnv.development
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000"
    PUBLIC_WEB_URL: str = "http://localhost:3000"
    PUBLIC_API_URL: str = "http://localhost:8000"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "zehno"
    POSTGRES_USER: str = "zehno"
    POSTGRES_PASSWORD: str = "zehno_dev_password"
    DATABASE_URL: str | None = None

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str | None = None
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    PASSWORD_HASH_SCHEME: str = "argon2"
    REFRESH_COOKIE_NAME: str = "zehno_refresh"
    REFRESH_COOKIE_SECURE: bool = False
    REFRESH_COOKIE_DOMAIN: str | None = None

    FIRST_SUPERADMIN_EMAIL: str = "admin@zehno.uz"
    FIRST_SUPERADMIN_PASSWORD: str = "Admin12345!"

    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_PUBLIC_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "zehno_minio"
    S3_SECRET_KEY: str = "zehno_minio_password"
    S3_BUCKET: str = "zehno"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = False

    VIDEO_PROVIDER: str = "mock"
    VIDEO_SIGNED_URL_TTL_MINUTES: int = 15

    PEERTUBE_BASE_URL: str = "http://localhost:9010"
    PEERTUBE_PUBLIC_URL: str = "http://localhost:9010"
    PEERTUBE_USERNAME: str | None = None
    PEERTUBE_PASSWORD: str | None = None
    PEERTUBE_CHANNEL_ID: str | None = None

    KINESCOPE_API_KEY: str | None = None
    KINESCOPE_PROJECT_ID: str | None = None

    BUNNY_STREAM_LIBRARY_ID: str | None = None
    BUNNY_STREAM_API_KEY: str | None = None
    BUNNY_STREAM_CDN_HOSTNAME: str | None = None
    BUNNY_STREAM_TOKEN_KEY: str | None = None

    PAYMENT_PROVIDER: str = "mock"
    PAYMENT_SANDBOX: bool = True
    PLATFORM_COMMISSION_PERCENT: int = 15

    PAYME_MERCHANT_ID: str | None = None
    PAYME_MERCHANT_KEY: str | None = None
    PAYME_CHECKOUT_URL: str = "https://checkout.paycom.uz"

    CLICK_MERCHANT_ID: str | None = None
    CLICK_SERVICE_ID: str | None = None
    CLICK_SECRET_KEY: str | None = None
    CLICK_MERCHANT_USER_ID: str | None = None
    CLICK_CHECKOUT_URL: str = "https://my.click.uz/services/pay"

    CRM_PROVIDER: str = "mock"
    BITRIX24_WEBHOOK_URL: str | None = None
    ESPOCRM_BASE_URL: str | None = None
    ESPOCRM_API_KEY: str | None = None

    TELEGRAM_ENABLED: bool = False
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_BOT_USERNAME: str | None = None
    TELEGRAM_WEBHOOK_SECRET: str | None = None

    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str = "Zehno <no-reply@zehno.uz>"

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "120/minute"
    RATE_LIMIT_AUTH: str = "10/minute"

    TESTING: bool = Field(default=False)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins(self) -> list[str]:
        raw = self.BACKEND_CORS_ORIGINS.strip()
        if not raw:
            return []
        if raw == "*":
            return ["*"]
        return [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_database_url(self) -> str:
        if self.DATABASE_URL:
            return _with_driver(self.DATABASE_URL, "postgresql+asyncpg")
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sync_database_url(self) -> str:
        if self.DATABASE_URL:
            return _with_driver(self.DATABASE_URL, "postgresql+psycopg")
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_dsn(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def celery_broker(self) -> str:
        return self.CELERY_BROKER_URL or f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def celery_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/2"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV is AppEnv.production


def _with_driver(dsn: str, driver: str) -> str:
    for prefix in (
        "postgresql+asyncpg://",
        "postgresql+psycopg://",
        "postgresql://",
        "postgres://",
    ):
        if dsn.startswith(prefix):
            return f"{driver}://{dsn[len(prefix) :]}"
    return dsn


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
