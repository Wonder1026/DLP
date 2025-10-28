from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Настройки приложения"""

    # App
    APP_NAME: str = "Corporate Messenger"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # DLP Settings
    DLP_ENABLED: bool = True
    OCR_LANGUAGE: str = "rus+eng"
    MAX_FILE_SIZE_MB: int = 50

    # Tesseract (для OCR)
    TESSERACT_CMD: Optional[str] = None

    # VirusTotal API
    VIRUSTOTAL_API_KEY: str = "your_api_key_here"  # ← добавили

    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()