# backend/app/db/crud/adoption.py
import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession


class AdoptionCRUD:
    async def has_active_application(
        self,
        db: AsyncSession,
        *,
        animal_id: str,
        user_id: uuid.UUID,
    ) -> bool:
        from app.db.models.adoption import Adoption

        aid = uuid.UUID(animal_id)
        r = await db.execute(
            select(Adoption).where(
                and_(
                    Adoption.animal_id == aid,
                    Adoption.applicant_id == user_id,
                    Adoption.is_active.is_(True),
                )
            )
        )
        return r.scalar_one_or_none() is not None

    async def create(self, db: AsyncSession, *, obj_in: dict):
        from app.db.models.adoption import Adoption

        obj = Adoption(**obj_in)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj


adoption_crud = AdoptionCRUD()
