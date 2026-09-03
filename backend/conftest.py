"""Fixtures compartilhadas da suíte do backend (M1+)."""
import pytest
from apps.accounts.models import Role, User
from django.core.management import call_command
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture(autouse=True)
def seeded_roles(db):
    """Garante papéis/permissões (doc 04) em cada teste que toca o banco."""
    call_command("seed_roles", verbosity=0)


@pytest.fixture
def make_user(db):
    def _make(*, email=None, password="SenhaForte123!", role_code="patient", **kwargs):
        email = email or f"{role_code}@exemplo.com"
        role = Role.objects.get(code=role_code)
        return User.objects.create_user(email=email, password=password, role=role, **kwargs)

    return _make


@pytest.fixture
def auth_client(db):
    """Retorna cliente autenticado por JWT para o usuário informado."""

    def _client(user):
        client = APIClient()
        token = str(RefreshToken.for_user(user).access_token)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client

    return _client


@pytest.fixture
def anon_client():
    return APIClient()
