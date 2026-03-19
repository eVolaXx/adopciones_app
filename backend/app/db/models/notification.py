# backend/app/db/models/notification.py
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.adoption import Adoption


class Notification(Base):
    __tablename__ = "notifications"

    # ── Clave primaria ─────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    # ── Relaciones FK ──────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        # CASCADE: si se borra el usuario, se borran sus notificaciones
    )
    adoption_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("adoptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        # SET NULL: si se borra la adopción, la notif queda huérfana pero no se pierde
    )

    # ── Tipo de evento ─────────────────────────────────────────
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        # Valores válidos:
        #   "adoption_new"       → nueva solicitud recibida (para admins)
        #   "status_changed"     → estado de tu solicitud cambió (para applicants)
        #   "adoption_approved"  → tu adopción fue aprobada
        #   "adoption_rejected"  → tu adopción fue rechazada
        #   "adoption_completed" → entrega del animal confirmada
        #   "message"            → mensaje libre del admin al solicitante
    )

    # ── Contenido ──────────────────────────────────────────────
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ── Estado de lectura ──────────────────────────────────────
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        # Indexado para poder hacer WHERE is_read = false eficientemente
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        # Se rellena cuando el usuario marca la notif como leída
    )

    # ── Auditoría ──────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relaciones ORM ─────────────────────────────────────────
    user: Mapped["User"] = relationship(
        "User",
        back_populates="notifications",
        lazy="noload",
        # noload: no cargar el user por defecto; se pide explícitamente si hace falta
    )
    adoption: Mapped["Adoption | None"] = relationship(
        "Adoption",
        back_populates="notifications",
        lazy="noload",
    )

    # ── Índice compuesto ───────────────────────────────────────
    __table_args__ = (
        Index(
            "ix_notifications_user_unread",
            "user_id", "is_read",
            # Optimiza la query más frecuente:
            # SELECT * FROM notifications WHERE user_id = ? AND is_read = false
        ),
    )

    # ── Método de conveniencia ─────────────────────────────────
    def mark_as_read(self) -> None:
        """Marcar como leída y registrar el timestamp."""
        self.is_read = True
        self.read_at = datetime.now(timezone.utc)

    # ── Repr para debugging ────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<Notification id={self.id} "
            f"type={self.type!r} "
            f"user_id={self.user_id} "
            f"is_read={self.is_read}>"
        )