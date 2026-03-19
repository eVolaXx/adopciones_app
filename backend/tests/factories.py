# backend/tests/factories.py
import uuid
from faker import Faker
from app.core.security import hash_password

fake = Faker("es_ES")


class ShelterFactory:
    @staticmethod
    def build(**kwargs) -> dict:
        """Devuelve un dict listo para pasarle a crud.shelter.create()"""
        return {
            "id": uuid.uuid4(),
            "name": kwargs.get("name", fake.company()),
            "type": kwargs.get("type", "protectora"),
            "email": kwargs.get("email", fake.unique.email()),
            "phone": kwargs.get("phone", fake.phone_number()[:20]),
            "city": kwargs.get("city", fake.city()),
            "address": kwargs.get("address", fake.address()),
            "is_active": kwargs.get("is_active", True),
        }


class UserFactory:
    @staticmethod
    def build(shelter_id=None, role="applicant", **kwargs) -> dict:
        return {
            "id": uuid.uuid4(),
            "shelter_id": shelter_id,
            "email": kwargs.get("email", fake.unique.email()),
            "hashed_password": hash_password(kwargs.get("password", "Test1234!")),
            "full_name": kwargs.get("full_name", fake.name()),
            "role": role,
            "phone": kwargs.get("phone", fake.phone_number()[:20]),
            "is_active": kwargs.get("is_active", True),
        }


class AnimalFactory:
    @staticmethod
    def build(shelter_id, **kwargs) -> dict:
        return {
            "id": uuid.uuid4(),
            "shelter_id": shelter_id,
            "name": kwargs.get("name", fake.first_name()),
            "breed": kwargs.get("breed", "Mestizo"),
            "age_months": kwargs.get("age_months", fake.random_int(min=1, max=120)),
            "size": kwargs.get("size", "mediano"),
            "sex": kwargs.get("sex", "macho"),
            "status": kwargs.get("status", "disponible"),
            "description": kwargs.get("description", fake.text(max_nb_chars=200)),
            "photos": kwargs.get("photos", []),
            "is_neutered": kwargs.get("is_neutered", False),
            "is_vaccinated": kwargs.get("is_vaccinated", True),
            "is_microchipped": kwargs.get("is_microchipped", False),
            "health_info": kwargs.get("health_info", {}),
            "character_tags": kwargs.get("character_tags", ["tranquilo"]),
            "adoption_requirements": kwargs.get("adoption_requirements", {}),
        }