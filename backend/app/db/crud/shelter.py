# backend/app/db/crud/shelter.py
import uuid

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession


class ShelterCRUD:
    async def delete(self, db: AsyncSession, *, id: str) -> None:
        from app.db.models.shelter import Shelter

        uid = uuid.UUID(id)
        await db.execute(delete(Shelter).where(Shelter.id == uid))
        await db.commit()


shelter_crud = ShelterCRUD()
