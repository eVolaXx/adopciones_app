# backend/app/db/schemas/animal.py
from pydantic import BaseModel, Field


class AnimalCreate(BaseModel):
    name: str
    breed: str
    age_months: int
    size: str
    sex: str
    weight_kg: float | None = None
    color: str | None = None
    description: str | None = None
    photos: list = Field(default_factory=list)
    is_neutered: bool = False
    is_vaccinated: bool = False
    is_microchipped: bool = False
    health_info: dict = Field(default_factory=dict)
    character_tags: list = Field(default_factory=list)
    adoption_requirements: dict = Field(default_factory=dict)
    status: str = "disponible"
