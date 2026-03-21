# backend/app/db/schemas/user.py
from pydantic import BaseModel, EmailStr, field_validator
import uuid

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return v

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    shelter_id: uuid.UUID | None
    is_active: bool

    model_config = {"from_attributes": True}  # permite crear desde objetos SQLAlchemy

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"