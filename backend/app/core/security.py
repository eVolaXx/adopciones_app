# backend/app/core/security.py
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# ── Contraseñas ────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# ── JWT ────────────────────────────────────────────────────────
def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload["type"] = "access"
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def create_refresh_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload["type"] = "refresh"
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ── Dependency: usuario actual ─────────────────────────────────
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Inyecta el usuario autenticado en cualquier endpoint.
    Uso: current_user = Depends(get_current_user)
    """
    from app.db.crud.user import user_crud   # import aquí para evitar circular

    payload = decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere un access token, no un refresh token",
        )

    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sin identificador de usuario",
        )

    user = await user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta desactivada — contacta con el administrador",
        )

    return user


# ── Dependency: usuario opcional (endpoints públicos) ──────────
async def get_current_user_optional(
    token: str = Depends(OAuth2PasswordBearer(
        tokenUrl="/api/v1/auth/login",
        auto_error=False,       # no lanza 401 si no hay token
    )),
    db: AsyncSession = Depends(get_db),
):
    """
    Para endpoints que funcionan con y sin token.
    Sin token devuelve None. Con token devuelve el usuario.
    Uso: current_user = Depends(get_current_user_optional)
    """
    if not token:
        return None
    try:
        return await get_current_user(token=token, db=db)
    except HTTPException:
        return None


# ── Dependency factory: control de roles ──────────────────────
def require_role(*roles: str):
    """
    Fábrica de dependencies para proteger endpoints por rol.

    Uso en endpoints:
        current_user = Depends(require_role("shelter_admin", "super_admin"))
        current_user = Depends(require_role("super_admin"))

    Lanza 403 si el usuario no tiene ninguno de los roles indicados.
    Lanza 401 si el token es inválido o no existe.
    """
    async def role_checker(
        current_user=Depends(get_current_user),
    ):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Acceso denegado. Se requiere uno de estos roles: "
                    f"{', '.join(roles)}. Tu rol actual: {current_user.role}"
                ),
            )
        return current_user

    return role_checker

# backend/app/core/security.py — añadir esta función de utilidad
def verify_shelter_ownership(current_user, resource_shelter_id):
    """
    Verifica que un shelter_admin solo opere sobre recursos de su propio shelter.
    El super_admin puede operar sobre cualquier shelter.

    Uso dentro de un endpoint:
        verify_shelter_ownership(current_user, animal.shelter_id)
    """
    if current_user.role == "super_admin":
        return  # super_admin pasa siempre

    if current_user.shelter_id != resource_shelter_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes modificar recursos de otra protectora",
        )
        
# ── Dependencies preconfiguradas (atajos convenientes) ─────────
# En lugar de escribir Depends(require_role("super_admin")) cada vez,
# importas directamente estas constantes en tus endpoints.

require_super_admin = require_role("super_admin")

require_shelter_admin = require_role("shelter_admin", "super_admin")
# super_admin puede hacer todo lo que hace shelter_admin

require_authenticated = get_current_user
# Alias semántico — cualquier usuario autenticado, sin restricción de rol