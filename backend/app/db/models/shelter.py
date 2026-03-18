# backend/app/db/models/shelter.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.crud.base import Base
from app.db.models.user import User
from app.db.models.animal import Animal


class Shelter(Base):
    __tablename__ = "shelters"

    # ── Clave primaria ─────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Datos de identificación ────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        # Valores válidos: "protectora" | "veterinaria"
    )

    # ── Contacto ───────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        nullable=False,
        index=True,
    )
    phone: Mapped[str | None] = mapped_column(String(20))
    website: Mapped[str | None] = mapped_column(String(300))

    # ── Dirección ──────────────────────────────────────────────
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100), index=True)
    province: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str | None] = mapped_column(String(10))

    # ── Imagen ─────────────────────────────────────────────────
    logo_url: Mapped[str | None] = mapped_column(Text)
    # URL devuelta por Cloudinary tras la subida

    # ── Estado ─────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── Auditoría ──────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relaciones ─────────────────────────────────────────────
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="shelter",
        lazy="selectin",       # carga automática en queries async
        cascade="all, delete-orphan",
    )
    animals: Mapped[list["Animal"]] = relationship(
        "Animal",
        back_populates="shelter",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    # ── Repr para debugging ────────────────────────────────────
    def __repr__(self) -> str:
        return f"<Shelter id={self.id} name={self.name!r} type={self.type!r}>"