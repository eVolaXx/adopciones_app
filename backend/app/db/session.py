# backend/app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,       # ponlo en True para ver el SQL en consola durante desarrollo
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    # expire_on_commit=False es importante en async: evita lazy loads
    # que fallarían fuera del contexto de la sesión
)