import bcrypt

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

