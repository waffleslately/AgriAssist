from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    PROJECT_NAME: str = "AgriAssist"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "dev-secret-key-change-in-production-1234567890"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database URLs
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "agri_db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agri_db"
    SYNC_DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/agri_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Google Earth Engine (GEE)
    GEE_ENABLED: bool = False
    GEE_SERVICE_ACCOUNT: str = ""
    GEE_PRIVATE_KEY: str = ""
    GEE_PROJECT_ID: str = ""

    # Weather
    WEATHER_PROVIDER: str = "open-meteo"

    # Default UI / Advisory Language (hi=Hindi, en=English, mr=Marathi, te=Telugu)
    DEFAULT_LANGUAGE: str = "hi"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]


settings = Settings()
