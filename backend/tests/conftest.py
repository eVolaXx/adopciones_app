# backend/tests/conftest.py
import asyncio
import os
import sys

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport

# Asegura que la carpeta backend esté en sys.path para que `import app...` funcione
BACKEND_ROOT = os.path.dirname(os.path.dirname(__file__))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.main import app
from app.db.base import Base
from app.core.config import settings
from app.core.dependencies import get_db

# ── URL de la BD de test ───────────────────────────────────────
# Usa una base de datos SEPARADA para tests, nunca la de desarrollo
TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    "/adopciones_db", "/adopciones_test"
)

# ── Engine async con NullPool ──────────────────────────────────
# NullPool es obligatorio en tests async: evita que conexiones
# abiertas en un test contaminen el siguiente
engine_test = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False,  # ponlo en True para ver el SQL generado en consola
)

TestingSessionLocal = async_sessionmaker(
    engine_test,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Event loop compartido por toda la sesión de tests ─────────
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── Crear/destruir tablas una vez por sesión ──────────────────
@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── Sesión de BD con rollback por test ─────────────────────────
# Cada test trabaja dentro de una transacción que se deshace al
# finalizar: la BD queda limpia sin necesidad de truncar tablas
@pytest_asyncio.fixture
async def db():
    async with engine_test.connect() as conn:
        await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        yield session
        await session.close()
        await conn.rollback()


# ── Override de get_db para inyectar la sesión de test ─────────
@pytest_asyncio.fixture
async def client(db: AsyncSession):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()