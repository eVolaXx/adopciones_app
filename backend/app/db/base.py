# backend/app/db/base.py
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Importar todos los modelos aquí para que Alembic los detecte automáticamente
from app.db.models.shelter import Shelter      # noqa: F401
from app.db.models.user import User            # noqa: F401
from app.db.models.animal import Animal        # noqa: F401
from app.db.models.adoption import Adoption    # noqa: F401
from app.db.models.notification import Notification  # noqa: F401