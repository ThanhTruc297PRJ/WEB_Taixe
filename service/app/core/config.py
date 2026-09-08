import os

from dotenv import load_dotenv

load_dotenv()


def _csv_env(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def _bool_env(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Driver Safety Monitoring API")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")

    FIREBASE_CREDENTIALS_PATH: str = os.getenv(
        "FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json"
    )
    FIREBASE_STORAGE_BUCKET: str = os.getenv("FIREBASE_STORAGE_BUCKET", "")

    CORS_ORIGINS: list[str] = _csv_env("CORS_ORIGINS", "http://localhost:5173")

    # B04 - API Gateway Security
    RATE_LIMIT_DEFAULT: str = os.getenv("RATE_LIMIT_DEFAULT", "60/minute")
    IP_WHITELIST_ENABLED: bool = _bool_env("IP_WHITELIST_ENABLED", False)
    IP_WHITELIST: list[str] = _csv_env("IP_WHITELIST", "127.0.0.1,::1")
    TRUST_PROXY_HEADERS: bool = _bool_env("TRUST_PROXY_HEADERS", False)


settings = Settings()
