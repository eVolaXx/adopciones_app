# backend/app/db/schemas/adoption.py
import uuid

from pydantic import BaseModel


class AdoptionCreate(BaseModel):
    animal_id: uuid.UUID
    message: str | None = None
