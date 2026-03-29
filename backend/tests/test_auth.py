# backend/tests/test_auth.py
import pytest
from httpx import AsyncClient

class TestRoleMiddleware:

    @pytest.mark.asyncio
    async def test_endpoint_publico_sin_token(self, client: AsyncClient):
        """El catálogo es accesible sin autenticación."""
        r = await client.get("/api/v1/animals")
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_endpoint_protegido_sin_token_da_401(self, client: AsyncClient):
        """Crear un animal sin token devuelve 401."""
        r = await client.post("/api/v1/animals", json={})
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_applicant_no_puede_crear_animal(
        self, client: AsyncClient, applicant_token: str
    ):
        """Un applicant autenticado no puede crear animales — debe dar 403."""
        r = await client.post(
            "/api/v1/animals",
            json={"name": "Rex", "breed": "Labrador",
                  "age_months": 12, "size": "grande", "sex": "macho"},
            headers={"Authorization": f"Bearer {applicant_token}"},
        )
        assert r.status_code == 403
        assert "roles" in r.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_shelter_admin_puede_crear_animal(
        self, client: AsyncClient, shelter_admin_token: str
    ):
        """Un shelter_admin sí puede crear animales."""
        r = await client.post(
            "/api/v1/animals",
            json={"name": "Rex", "breed": "Labrador",
                  "age_months": 12, "size": "grande", "sex": "macho"},
            headers={"Authorization": f"Bearer {shelter_admin_token}"},
        )
        assert r.status_code == 201

    @pytest.mark.asyncio
    async def test_token_expirado_da_401(self, client: AsyncClient):
        """Un token expirado devuelve 401."""
        from jose import jwt
        from app.core.config import settings
        from datetime import datetime, timezone, timedelta

        expired_token = jwt.encode(
            {"sub": "fake-id", "role": "shelter_admin", "type": "access",
             "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
            settings.SECRET_KEY, algorithm="HS256"
        )
        r = await client.post(
            "/api/v1/animals", json={},
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_no_vale_como_access(self, client: AsyncClient):
        """Un refresh token no debe poder usarse para acceder a endpoints."""
        from app.core.security import create_refresh_token
        bad_token = create_refresh_token({"sub": "fake-id", "role": "shelter_admin"})
        r = await client.post(
            "/api/v1/animals", json={},
            headers={"Authorization": f"Bearer {bad_token}"},
        )
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_shelter_admin_no_puede_editar_animal_de_otro_shelter(
        self, client: AsyncClient, shelter_admin_token: str, animal_otro_shelter
    ):
        """Un admin no puede editar animales que no son de su shelter."""
        r = await client.put(
            f"/api/v1/animals/{animal_otro_shelter.id}",
            json={"name": "Nuevo nombre"},
            headers={"Authorization": f"Bearer {shelter_admin_token}"},
        )
        assert r.status_code == 403
        assert "protectora" in r.json()["detail"].lower()