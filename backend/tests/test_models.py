# backend/tests/test_models.py
import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models.shelter import Shelter
from app.db.models.user import User
from app.db.models.animal import Animal
from tests.factories import ShelterFactory, UserFactory, AnimalFactory




# ════════════════════════════════════════════════════════════════
# FIXTURES LOCALES
# ════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def shelter(db: AsyncSession) -> Shelter:
    """Shelter persistido, disponible para cualquier test de este módulo."""
    obj = Shelter(**ShelterFactory.build())
    db.add(obj)
    await db.flush()   # flush en vez de commit: respeta el rollback del conftest
    return obj


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession, shelter: Shelter) -> User:
    obj = User(**UserFactory.build(shelter_id=shelter.id, role="shelter_admin"))
    db.add(obj)
    await db.flush()
    return obj


@pytest_asyncio.fixture
async def animal(db: AsyncSession, shelter: Shelter) -> Animal:
    obj = Animal(**AnimalFactory.build(shelter_id=shelter.id))
    db.add(obj)
    await db.flush()
    return obj


# ════════════════════════════════════════════════════════════════
# TESTS: MODELO SHELTER
# ════════════════════════════════════════════════════════════════

class TestShelterModel:

    @pytest.mark.asyncio
    async def test_crear_shelter_basico(self, db: AsyncSession):
        """Un shelter con datos mínimos válidos se persiste correctamente."""
        data = ShelterFactory.build(name="Protectora Los Amigos", type="protectora")
        obj = Shelter(**data)
        db.add(obj)
        await db.flush()

        result = await db.get(Shelter, obj.id)
        assert result is not None
        assert result.name == "Protectora Los Amigos"
        assert result.type == "protectora"
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_shelter_email_unico(self, db: AsyncSession, shelter: Shelter):
        """Dos shelters con el mismo email violan la constraint UNIQUE."""
        duplicado = Shelter(**ShelterFactory.build(email=shelter.email))
        db.add(duplicado)
        with pytest.raises(IntegrityError, match="unique"):
            await db.flush()

    @pytest.mark.asyncio
    async def test_shelter_email_obligatorio(self, db: AsyncSession):
        """Un shelter sin email no puede persistirse."""
        data = ShelterFactory.build()
        data.pop("email")
        obj = Shelter(**data)
        db.add(obj)
        with pytest.raises(IntegrityError):
            await db.flush()

    @pytest.mark.asyncio
    async def test_shelter_created_at_se_rellena_automaticamente(self, db: AsyncSession):
        obj = Shelter(**ShelterFactory.build())
        db.add(obj)
        await db.flush()
        assert obj.created_at is not None

    @pytest.mark.asyncio
    async def test_shelter_updated_at_cambia_al_modificar(self, db: AsyncSession, shelter: Shelter):
        original_updated = shelter.updated_at
        shelter.city = "Madrid"
        await db.flush()
        await db.refresh(shelter)
        # updated_at debe ser >= al original tras la modificación
        assert shelter.updated_at >= original_updated

    @pytest.mark.asyncio
    async def test_shelter_repr(self, shelter: Shelter):
        r = repr(shelter)
        assert "Shelter" in r
        assert shelter.name in r

    @pytest.mark.asyncio
    async def test_shelter_tipos_validos(self, db: AsyncSession):
        """Verifica que se pueden crear los dos tipos permitidos."""
        for tipo in ("protectora", "veterinaria"):
            obj = Shelter(**ShelterFactory.build(type=tipo))
            db.add(obj)
            await db.flush()
            assert obj.type == tipo

    @pytest.mark.asyncio
    async def test_listar_shelters_activos(self, db: AsyncSession):
        activo = Shelter(**ShelterFactory.build(is_active=True))
        inactivo = Shelter(**ShelterFactory.build(is_active=False))
        db.add_all([activo, inactivo])
        await db.flush()

        result = await db.execute(
            select(Shelter).where(Shelter.is_active == True)
        )
        activos = result.scalars().all()
        ids_activos = [s.id for s in activos]

        assert activo.id in ids_activos
        assert inactivo.id not in ids_activos


# ════════════════════════════════════════════════════════════════
# TESTS: MODELO USER
# ════════════════════════════════════════════════════════════════

class TestUserModel:

    @pytest.mark.asyncio
    async def test_crear_user_applicant(self, db: AsyncSession):
        """Un applicant no necesita shelter_id."""
        data = UserFactory.build(role="applicant", shelter_id=None)
        obj = User(**data)
        db.add(obj)
        await db.flush()

        result = await db.get(User, obj.id)
        assert result.role == "applicant"
        assert result.shelter_id is None

    @pytest.mark.asyncio
    async def test_crear_shelter_admin_con_shelter(self, db: AsyncSession, shelter: Shelter):
        """Un shelter_admin debe estar vinculado a un shelter."""
        data = UserFactory.build(role="shelter_admin", shelter_id=shelter.id)
        obj = User(**data)
        db.add(obj)
        await db.flush()

        result = await db.get(User, obj.id)
        assert result.shelter_id == shelter.id
        assert result.role == "shelter_admin"

    @pytest.mark.asyncio
    async def test_user_email_unico(self, db: AsyncSession, admin_user: User):
        duplicado = User(**UserFactory.build(email=admin_user.email))
        db.add(duplicado)
        with pytest.raises(IntegrityError, match="unique"):
            await db.flush()

    @pytest.mark.asyncio
    async def test_password_se_guarda_hasheada(self, db: AsyncSession):
        """La contraseña jamás se almacena en texto plano."""
        data = UserFactory.build(password="MiPasswordSegura99!")
        obj = User(**data)
        db.add(obj)
        await db.flush()

        result = await db.get(User, obj.id)
        assert result.hashed_password != "MiPasswordSegura99!"
        assert result.hashed_password.startswith("$2b$")  # prefijo bcrypt

    @pytest.mark.asyncio
    async def test_user_is_active_por_defecto(self, db: AsyncSession):
        obj = User(**UserFactory.build())
        db.add(obj)
        await db.flush()
        assert obj.is_active is True

    @pytest.mark.asyncio
    async def test_user_fk_shelter_invalido(self, db: AsyncSession):
        """FK a un shelter inexistente viola la integridad referencial."""
        data = UserFactory.build(shelter_id=uuid.uuid4())  # ID que no existe
        obj = User(**data)
        db.add(obj)
        with pytest.raises(IntegrityError, match="foreign key"):
            await db.flush()

    @pytest.mark.asyncio
    async def test_borrar_shelter_cascade_users(self, db: AsyncSession):
        """Al borrar un shelter, sus usuarios se borran en cascada."""
        s = Shelter(**ShelterFactory.build())
        db.add(s)
        await db.flush()

        u = User(**UserFactory.build(shelter_id=s.id, role="shelter_admin"))
        db.add(u)
        await db.flush()
        user_id = u.id

        await db.delete(s)
        await db.flush()

        deleted_user = await db.get(User, user_id)
        assert deleted_user is None


# ════════════════════════════════════════════════════════════════
# TESTS: MODELO ANIMAL
# ════════════════════════════════════════════════════════════════

class TestAnimalModel:

    @pytest.mark.asyncio
    async def test_crear_animal_basico(self, db: AsyncSession, shelter: Shelter):
        data = AnimalFactory.build(shelter_id=shelter.id, name="Rocky")
        obj = Animal(**data)
        db.add(obj)
        await db.flush()

        result = await db.get(Animal, obj.id)
        assert result.name == "Rocky"
        assert result.status == "disponible"

    @pytest.mark.asyncio
    async def test_animal_status_por_defecto_es_disponible(self, db: AsyncSession, shelter: Shelter):
        data = AnimalFactory.build(shelter_id=shelter.id)
        data.pop("status", None)
        obj = Animal(**data)
        db.add(obj)
        await db.flush()
        assert obj.status == "disponible"

    @pytest.mark.asyncio
    async def test_animal_status_invalido_viola_constraint(self, db: AsyncSession, shelter: Shelter):
        """La CheckConstraint de PostgreSQL rechaza status fuera del enum."""
        data = AnimalFactory.build(shelter_id=shelter.id, status="perdido")
        obj = Animal(**data)
        db.add(obj)
        with pytest.raises(IntegrityError, match="ck_animals_status"):
            await db.flush()

    @pytest.mark.asyncio
    async def test_animal_size_invalido_viola_constraint(self, db: AsyncSession, shelter: Shelter):
        data = AnimalFactory.build(shelter_id=shelter.id, size="gigante")
        obj = Animal(**data)
        db.add(obj)
        with pytest.raises(IntegrityError, match="ck_animals_size"):
            await db.flush()

    @pytest.mark.asyncio
    async def test_animal_sex_invalido_viola_constraint(self, db: AsyncSession, shelter: Shelter):
        data = AnimalFactory.build(shelter_id=shelter.id, sex="desconocido")
        obj = Animal(**data)
        db.add(obj)
        with pytest.raises(IntegrityError, match="ck_animals_sex"):
            await db.flush()

    @pytest.mark.asyncio
    async def test_animal_age_negativo_viola_constraint(self, db: AsyncSession, shelter: Shelter):
        data = AnimalFactory.build(shelter_id=shelter.id, age_months=-1)
        obj = Animal(**data)
        db.add(obj)
        with pytest.raises(IntegrityError, match="ck_animals_age_positive"):
            await db.flush()

    @pytest.mark.asyncio
    async def test_animal_photos_es_lista_vacia_por_defecto(self, db: AsyncSession, shelter: Shelter):
        data = AnimalFactory.build(shelter_id=shelter.id)
        data.pop("photos", None)
        obj = Animal(**data)
        db.add(obj)
        await db.flush()
        assert obj.photos == []

    @pytest.mark.asyncio
    async def test_animal_health_info_jsonb(self, db: AsyncSession, shelter: Shelter):
        """JSONB acepta estructuras anidadas arbitrarias."""
        health = {
            "vacunas": ["rabia", "moquillo"],
            "ultima_revision": "2024-11-10",
            "condiciones": [],
            "medicacion": None,
        }
        data = AnimalFactory.build(shelter_id=shelter.id, health_info=health)
        obj = Animal(**data)
        db.add(obj)
        await db.flush()

        result = await db.get(Animal, obj.id)
        assert result.health_info["vacunas"] == ["rabia", "moquillo"]
        assert result.health_info["medicacion"] is None

    @pytest.mark.asyncio
    async def test_animal_character_tags_jsonb(self, db: AsyncSession, shelter: Shelter):
        tags = ["juguetón", "bueno con niños", "no compatible con gatos"]
        data = AnimalFactory.build(shelter_id=shelter.id, character_tags=tags)
        obj = Animal(**data)
        db.add(obj)
        await db.flush()

        result = await db.get(Animal, obj.id)
        assert "juguetón" in result.character_tags
        assert len(result.character_tags) == 3

    # ── Propiedades calculadas ────────────────────────────────

    @pytest.mark.asyncio
    async def test_age_display_meses(self, db: AsyncSession, shelter: Shelter):
        obj = Animal(**AnimalFactory.build(shelter_id=shelter.id, age_months=3))
        assert obj.age_display == "3 meses"

    @pytest.mark.asyncio
    async def test_age_display_un_mes(self, db: AsyncSession, shelter: Shelter):
        obj = Animal(**AnimalFactory.build(shelter_id=shelter.id, age_months=1))
        assert obj.age_display == "1 mes"

    @pytest.mark.asyncio
    async def test_age_display_anos_exactos(self, db: AsyncSession, shelter: Shelter):
        obj = Animal(**AnimalFactory.build(shelter_id=shelter.id, age_months=24))
        assert obj.age_display == "2 años"

    @pytest.mark.asyncio
    async def test_age_display_anos_y_meses(self, db: AsyncSession, shelter: Shelter):
        obj = Animal(**AnimalFactory.build(shelter_id=shelter.id, age_months=14))
        assert obj.age_display == "1 año y 2 meses"

    @pytest.mark.asyncio
    async def test_main_photo_primera_url(self, db: AsyncSession, shelter: Shelter):
        fotos = ["https://cdn.cloudinary.com/foto1.jpg", "https://cdn.cloudinary.com/foto2.jpg"]
        obj = Animal(**AnimalFactory.build(shelter_id=shelter.id, photos=fotos))
        assert obj.main_photo == "https://cdn.cloudinary.com/foto1.jpg"

    @pytest.mark.asyncio
    async def test_main_photo_sin_fotos_devuelve_none(self, db: AsyncSession, shelter: Shelter):
        obj = Animal(**AnimalFactory.build(shelter_id=shelter.id, photos=[]))
        assert obj.main_photo is None

    @pytest.mark.asyncio
    async def test_is_available(self, db: AsyncSession, shelter: Shelter):
        disponible = Animal(**AnimalFactory.build(shelter_id=shelter.id, status="disponible"))
        adoptado = Animal(**AnimalFactory.build(shelter_id=shelter.id, status="adoptado"))
        assert disponible.is_available is True
        assert adoptado.is_available is False

    # ── Queries con filtros ───────────────────────────────────

    @pytest.mark.asyncio
    async def test_filtrar_por_status(self, db: AsyncSession, shelter: Shelter):
        db.add(Animal(**AnimalFactory.build(shelter_id=shelter.id, status="disponible")))
        db.add(Animal(**AnimalFactory.build(shelter_id=shelter.id, status="adoptado")))
        db.add(Animal(**AnimalFactory.build(shelter_id=shelter.id, status="disponible")))
        await db.flush()

        result = await db.execute(
            select(Animal).where(
                Animal.shelter_id == shelter.id,
                Animal.status == "disponible",
            )
        )
        disponibles = result.scalars().all()
        assert len(disponibles) == 2
        assert all(a.status == "disponible" for a in disponibles)

    @pytest.mark.asyncio
    async def test_filtrar_por_size(self, db: AsyncSession, shelter: Shelter):
        db.add(Animal(**AnimalFactory.build(shelter_id=shelter.id, size="pequeño")))
        db.add(Animal(**AnimalFactory.build(shelter_id=shelter.id, size="grande")))
        await db.flush()

        result = await db.execute(
            select(Animal).where(
                Animal.shelter_id == shelter.id,
                Animal.size == "pequeño",
            )
        )
        assert len(result.scalars().all()) == 1

    @pytest.mark.asyncio
    async def test_borrar_shelter_cascade_animals(self, db: AsyncSession):
        """Al borrar un shelter, sus animales se borran en cascada."""
        s = Shelter(**ShelterFactory.build())
        db.add(s)
        await db.flush()

        a = Animal(**AnimalFactory.build(shelter_id=s.id))
        db.add(a)
        await db.flush()
        animal_id = a.id

        await db.delete(s)
        await db.flush()

        assert await db.get(Animal, animal_id) is None