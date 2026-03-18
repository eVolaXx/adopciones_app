# backend/app/db/models/user.py
import uuid
from sqlalchemy import String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from backend.app.db.base import Base
from app.db.models.shelter import Shelter
from app.db.models.adoption import Adoption
from app.db.models.notification import Notification



class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    shelter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("shelters.id", ondelete="SET NULL"), nullable=True
    )
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(500), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(30), default="applicant")
    # roles válidos: "super_admin" | "shelter_admin" | "applicant"
    phone: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    shelter: Mapped["Shelter | None"] = relationship(back_populates="users")
    adoptions: Mapped[list["Adoption"]] = relationship(back_populates="applicant")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user")