from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    PROJECT_NAME: str = "13F Browser"
    VERSION: str = "1.0.0"

    # Base Project Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    EDGAR_DIR: Path = BASE_DIR / "EDGAR"

    # Database
    DATABASE_URL: str = "sqlite:///./13f_data.db"

    class Config:
        env_file = ".env"


settings = Settings()
