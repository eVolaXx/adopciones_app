# backend/scripts/create_test_db.py
import asyncio
import asyncpg
from app.core.config import settings

async def main():
    # Conectar a la BD principal para poder crear la de test
    conn = await asyncpg.connect(settings.DATABASE_URL.replace(
        "+asyncpg", ""  # asyncpg directo no necesita el dialecto SQLAlchemy
    ))
    try:
        await conn.execute("CREATE DATABASE adopciones_test")
        print("BD adopciones_test creada correctamente")
    except asyncpg.DuplicateDatabaseError:
        print("La BD adopciones_test ya existe, continuando...")
    finally:
        await conn.close()

asyncio.run(main())