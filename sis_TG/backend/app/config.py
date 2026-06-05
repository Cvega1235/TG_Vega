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
    TRIPADVISOR_API_KEY: str = ""

    # SMTP / Email (Gmail)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""

    # OTP
    OTP_EXPIRE_MINUTES: int = 5

    # Seguridad — cifrado de campos sensibles
    # Generar con: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    ENCRYPTION_KEY: str = ""

    # Clave para descifrar datos de recetas (recipes.enc)
    RECIPE_KEY: str = ""

    # Bloqueo de cuenta por intentos fallidos
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_MINUTES: int = 30

    # Timeout de inactividad (enviado al frontend como referencia)
    INACTIVITY_TIMEOUT_MINUTES: int = 30

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
