# backend/app/db/crud/animal.py
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class AnimalCRUD:
    async def get_catalog(self, db: AsyncSession):
        from app.db.models.animal import Animal

        r = await db.execute(select(Animal).where(Animal.status == "disponible"))
        return list(r.scalars().all())

    async def get(self, db: AsyncSession, animal_id: str):
        from app.db.models.animal import Animal

        uid = uuid.UUID(animal_id)
        r = await db.execute(select(Animal).where(Animal.id == uid))
        return r.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: dict):
        from app.db.models.animal import Animal

        defaults = {
            "photos": [],
            "health_info": {},
            "character_tags": [],
            "adoption_requirements": {},
        }
        data = {**defaults, **obj_in}
        obj = Animal(**data)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj


animal_crud = AnimalCRUD()
