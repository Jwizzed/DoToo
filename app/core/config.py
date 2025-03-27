from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    PROJECT_NAME: str = "Todo Application"
    API_V1_STR: str = "/api/v1"

    # Database settings
    DATABASE_URL: str

    # JWT settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Optional: File Upload settings
    STATIC_DIR: Path = BASE_DIR / "app" / "static"
    IMAGES_DIR: Path = STATIC_DIR / "images"
    IMAGE_BASE_URL: str = "http://localhost:8000/static/images/"

    def __init__(self, **values):
        super().__init__(**values)
        self.STATIC_DIR.mkdir(parents=True, exist_ok=True)
        self.IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    model_config = SettingsConfigDict(
        env_file=f"{BASE_DIR}/.env",
        case_sensitive=True,
        extra='ignore'  # Ignore extra fields from .env if any
    )


@lru_cache()  # Cache the settings object for performance
def get_settings() -> Settings:
    """Returns the application settings."""
    return Settings()


settings = get_settings()
