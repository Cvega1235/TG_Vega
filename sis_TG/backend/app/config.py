from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://don_piotr:password@localhost:5432/don_piotr_db"
    SECRET_KEY: str = "change-this-to-a-random-64-character-string"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: str = "http://localhost:5173"
    SUPERADMIN_EMAIL: str = "admin@donpiotr.com"
    SUPERADMIN_PASSWORD: str = "admin123"
    ALGORITHM: str = "HS256"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
