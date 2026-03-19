import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.animal import Animal
    from app.db.models.notification import Notification


class Adoption(Base):
    __tablename__ = "adoptions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    animal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("animals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    applicant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
        # Valores esperados (puedes ajustarlos en migraciones/lógica):
        # "pending" | "in_review" | "approved" | "rejected" | "completed"
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

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
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    animal: Mapped["Animal"] = relationship(
        "Animal",
        back_populates="adoptions",
        lazy="selectin",
    )
    applicant: Mapped["User"] = relationship(
        "User",
        back_populates="adoptions",
        lazy="selectin",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="adoption",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return (
            f"<Adoption id={self.id} "
            f"animal_id={self.animal_id} "
            f"applicant_id={self.applicant_id} "
            f"status={self.status!r}>"
        )