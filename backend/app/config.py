"""Environment Secrets Management for SafeHabitat AI.

Loads secrets from environment, .env file, or AWS Secrets Manager.
"""
import os
import json
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database
    DATABASE_URL: str = "sqlite:///./safehabitat.db"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480

    # External APIs
    BHUVAN_API_KEY: str = ""
    BHUVAN_BASE_URL: str = "https://bhuvan.nrsc.gov.in"
    IMD_API_KEY: str = ""
    IMD_BASE_URL: str = "https://api.imd.gov.in"
    CWC_API_KEY: str = ""
    CWC_BASE_URL: str = "https://cwc.gov.in"

    # AWS (for production)
    AWS_REGION: str = "ap-south-1"
    AWS_SECRETS_NAME: str = "safehabitat/prod"

    # Monitoring
    SENTRY_DSN: str = ""
    LOG_LEVEL: str = "INFO"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def load_secrets_from_aws() -> dict:
    """Load secrets from AWS Secrets Manager."""
    try:
        import boto3
        client = boto3.client("secretsmanager", region_name=os.getenv("AWS_REGION", "ap-south-1"))
        response = client.get_secret_value(SecretId=os.getenv("AWS_SECRETS_NAME", "safehabitat/prod"))
        return json.loads(response["SecretString"])
    except Exception:
        return {}


def load_dotenv():
    """Load .env file if present."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())
