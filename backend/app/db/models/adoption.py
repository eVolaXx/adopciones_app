# backend/app/db/models/animal.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Boolean, Text, DateTime,
    Integer, ForeignKey, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.db.models.shelter import Shelter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.db.models.adoption import Adoption


class Animal(Base):
    __tablename__ = "animals"

    # ── Clave primaria ─────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── FK al shelter propietario ──────────────────────────────
    shelter_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("shelters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Datos básicos ──────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    breed: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        # "Mestizo" si no se conoce la raza exacta
    )
    age_months: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        # Almacenar en meses permite precisión con cachorros
        # (3 meses vs "0 años") y facilita filtros por rango
    )
    size: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        # Valores: "pequeño" | "mediano" | "grande"
    )
    sex: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        # Valores: "macho" | "hembra"
    )
    weight_kg: Mapped[float | None] = mapped_column(
        nullable=True,
        # Peso aproximado en kg, opcional
    )
    color: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # ── Estado en el sistema ───────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="disponible",
        index=True,
        # Valores:
        #   "disponible"  → visible en el catálogo público
        #   "en_proceso"  → tiene al menos una solicitud activa
        #   "adoptado"    → adopción completada, sale del catálogo
        #   "eliminado"   → soft delete, nunca se borra físicamente
    )

    # ── Descripción ────────────────────────────────────────────
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        # Texto libre: carácter, historia, necesidades especiales
    )

    # ── Fotos ──────────────────────────────────────────────────
    photos: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        # Array de URLs de Cloudinary, ordenadas por posición
        # Ejemplo: ["https://res.cloudinary.com/.../foto1.jpg", ...]
        # La primera URL se usa como foto principal en el catálogo
    )

    # ── Salud ──────────────────────────────────────────────────
    is_neutered: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_vaccinated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_microchipped: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    health_info: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        # Datos semiestructurados de salud. Ejemplo:
        # {
        #   "vacunas": ["rabia", "moquillo", "parvovirus"],
        #   "ultima_revision": "2024-11-10",
        #   "condiciones": ["displasia leve"],
        #   "medicacion": null,
        #   "notas_vet": "Revisión anual al día"
        # }
    )

    # ── Carácter y compatibilidades ────────────────────────────
    character_tags: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        # Array de strings de libre elección por el admin.
        # Ejemplos: ["juguetón", "tranquilo", "sociable",
        #            "bueno con niños", "no compatible con gatos"]
    )

    # ── Requisitos para la adopción ────────────────────────────
    adoption_requirements: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        # Requisitos específicos del animal. Ejemplo:
        # {
        #   "jardin_obligatorio": True,
        #   "familia_sin_ninos": False,
        #   "experiencia_previa": False,
        #   "notas": "Necesita espacio para correr"
        # }
    )

    # ── Auditoría ──────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    adopted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        # Se rellena cuando la adopción se marca como completada
    )

    # ── Relaciones ORM ─────────────────────────────────────────
    shelter: Mapped["Shelter"] = relationship(
        "Shelter",
        back_populates="animals",
        lazy="noload",
        # noload: el shelter no se carga automáticamente.
        # En el catálogo público no se necesita; se pide
        # explícitamente solo cuando hace falta (ficha detalle).
    )
    adoptions: Mapped[list["Adoption"]] = relationship(
        "Adoption",
        back_populates="animal",
        lazy="noload",
        # Las adopciones solo se cargan en el panel de admin,
        # nunca en el catálogo público.
    )

    # ── Constraints de base de datos ───────────────────────────
    __table_args__ = (
        CheckConstraint(
            "status IN ('disponible','en_proceso','adoptado','eliminado')",
            name="ck_animals_status",
        ),
        CheckConstraint(
            "size IN ('pequeño','mediano','grande')",
            name="ck_animals_size",
        ),
        CheckConstraint(
            "sex IN ('macho','hembra')",
            name="ck_animals_sex",
        ),
        CheckConstraint(
            "age_months >= 0",
            name="ck_animals_age_positive",
        ),
        # Índice compuesto para el catálogo público:
        # la query más frecuente filtra por status + shelter_id
        Index(
            "ix_animals_shelter_status",
            "shelter_id", "status",
        ),
        # Índice para búsquedas por ciudad (via JOIN con shelter)
        # se añade en la migración a nivel de query, no aquí
    )

    # ── Propiedades calculadas ─────────────────────────────────
    @property
    def age_display(self) -> str:
        """Convierte age_months a texto legible para el frontend."""
        if self.age_months < 1:
            return "Menos de 1 mes"
        if self.age_months < 12:
            return f"{self.age_months} {'mes' if self.age_months == 1 else 'meses'}"
        years = self.age_months // 12
        months = self.age_months % 12
        base = f"{years} {'año' if years == 1 else 'años'}"
        if months:
            base += f" y {months} {'mes' if months == 1 else 'meses'}"
        return base

    @property
    def main_photo(self) -> str | None:
        """Primera foto del array, usada como thumbnail en el catálogo."""
        return self.photos[0] if self.photos else None

    @property
    def is_available(self) -> bool:
        return self.status == "disponible"

    # ── Repr para debugging ────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<Animal id={self.id} "
            f"name={self.name!r} "
            f"breed={self.breed!r} "
            f"status={self.status!r}>"
        )