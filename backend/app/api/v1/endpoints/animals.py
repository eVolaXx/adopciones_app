# backend/app/api/v1/endpoints/animals.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import (
    require_super_admin,
    require_shelter_admin,
    require_authenticated,
    get_current_user_optional,
)
from app.db.crud.animal import animal_crud
from app.db.crud.adoption import adoption_crud
from app.db.crud.shelter import shelter_crud
from app.db.schemas.adoption import AdoptionCreate
from app.db.schemas.animal import AnimalCreate

router = APIRouter(prefix="/animals", tags=["animals"])

# ── 1. Endpoint público — sin token ───────────────────────────
@router.get("")
async def list_animals(db: AsyncSession = Depends(get_db)):
    # Cualquiera puede ver el catálogo, ni siquiera necesita cuenta
    return await animal_crud.get_catalog(db)


# ── 2. Endpoint público con info extra si hay sesión ──────────
@router.get("/{animal_id}")
async def get_animal(
    animal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    animal = await animal_crud.get(db, animal_id)
    if not animal:
        raise HTTPException(404, "Animal no encontrado")

    # Si hay sesión, incluir si el usuario ya solicitó este animal
    if current_user:
        animal.already_applied = await adoption_crud.has_active_application(
            db, animal_id=animal_id, user_id=current_user.id
        )
    return animal


# ── 3. Solo usuarios autenticados (cualquier rol) ─────────────
@router.post("/adoptions")
async def create_adoption(
    adoption_in: AdoptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_authenticated),  # login obligatorio
):
    return await adoption_crud.create(db, obj_in={
        **adoption_in.model_dump(),
        "applicant_id": current_user.id,
    })


# ── 4. Solo shelter_admin o superior ─────────────────────────
@router.post("")
async def create_animal(
    animal_in: AnimalCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_shelter_admin),  # shelter_admin + super_admin
):
    # Asignar automáticamente al shelter del admin que lo crea
    return await animal_crud.create(db, obj_in={
        **animal_in.model_dump(),
        "shelter_id": current_user.shelter_id,
    })


# ── 5. Solo super_admin ───────────────────────────────────────
@router.delete("/shelters/{shelter_id}")
async def delete_shelter(
    shelter_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_super_admin),  # solo super_admin
):
    await shelter_crud.delete(db, id=shelter_id)