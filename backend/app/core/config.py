# backend/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Base de datos
    DATABASE_URL: str = "postgresql+asyncpg://admin:secretpass@localhost/adopciones_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # JWT — genera uno fuerte con: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str = "cambia-esto-en-produccion"

    # Cloudinary (para la Fase 2)
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # SendGrid (para la Fase 2)
    SENDGRID_API_KEY: str = ""

    class Config:
        env_file = ".env"  # lee automáticamente el archivo .env

settings = Settings()  # instancia global que importan el resto de módulos