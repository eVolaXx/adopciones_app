# backend/app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import crud
from app.db.schemas.user import UserCreate, UserResponse, TokenResponse
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token, get_current_user
)
from app.core.dependencies import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Verificar que el email no exista ya
    existing = await crud.user.get_by_email(db, email=user_in.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email ya registrado")

    user = await crud.user.create(db, obj_in={
        **user_in.model_dump(exclude={"password"}),
        "hashed_password": hash_password(user_in.password),
        "role": "applicant",  # rol por defecto
    })
    return user

@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),  # espera username + password
    db: AsyncSession = Depends(get_db)
):
    user = await crud.user.get_by_email(db, email=form.username)
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")

    token_data = {"sub": str(user.id), "role": user.role}
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
    }

@router.post("/refresh", response_model=TokenResponse)
async def refresh(refresh_token: str, db: AsyncSession = Depends(get_db)):
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token inválido")
    token_data = {"sub": payload["sub"], "role": payload["role"]}
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
    }

@router.get("/me", response_model=UserResponse)
async def get_me(current_user = Depends(get_current_user)):
    return current_user  # FastAPI extrae el token del header automáticamente