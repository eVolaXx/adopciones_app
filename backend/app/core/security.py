import bcrypt
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.dependencies import get_db
from app.db import crud

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Bcrypt limita la longitud del "password" a 72 bytes.
_BCRYPT_MAX_PASSWORD_BYTES = 72


def _truncate_password(password: str) -> bytes:
    # Recortamos en bytes para cumplir la limitación de bcrypt.
    password_bytes = password.encode("utf-8")
    return password_bytes[:_BCRYPT_MAX_PASSWORD_BYTES]


def hash_password(password: str) -> str:
    """Hashea una contraseña usando bcrypt (evita passlib)."""
    hashed = bcrypt.hashpw(_truncate_password(password), bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica que una contraseña en texto plano coincide con el hash almacenado."""
    return bcrypt.checkpw(
        _truncate_password(plain_password),
        hashed_password.encode("utf-8"),
    )

# ── JWT ────────────────────────────────────────────────────────
def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=30)
    payload["type"] = "access"
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def create_refresh_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(days=7)
    payload["type"] = "refresh"
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

# ── Dependency injection ───────────────────────────────────────
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token sin identificador")
    user = await crud.user.get(db, id=user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")
    return user

# Dependency para rutas que requieren rol específico
def require_role(*roles: str):
    async def checker(current_user = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Sin permisos suficientes")
        return current_user
    return checker

