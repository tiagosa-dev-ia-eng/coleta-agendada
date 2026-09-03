"""Testes RBAC (doc 14 §3) — acesso cruzado entre perfis deve retornar 403."""
import pytest
from django.core.management import call_command

from apps.accounts.models import Permission, Role

USERS = "/api/v1/users"
PASSWORD = "SenhaForte123!"


def _create_payload(**over):
    payload = {
        "email": "novo@exemplo.com",
        "password": PASSWORD,
        "first_name": "Novo",
        "role_code": "technician",
    }
    payload.update(over)
    return payload


def test_laboratory_lists_users(make_user, auth_client):
    lab = make_user(role_code="laboratory", email="lab@exemplo.com")
    make_user(role_code="patient", email="pac@exemplo.com")
    client = auth_client(lab)
    resp = client.get(USERS)
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.json()["results"]]
    assert "lab@exemplo.com" in emails
    assert "pac@exemplo.com" in emails


@pytest.mark.parametrize(
    "role_code",
    ["patient", "technician", "pharmacy", "reseller"],
)
def test_non_managers_cannot_list_users(role_code, make_user, auth_client):
    user = make_user(role_code=role_code)
    client = auth_client(user)
    resp = client.get(USERS)
    assert resp.status_code == 403


@pytest.mark.parametrize(
    "role_code",
    ["patient", "technician", "pharmacy", "reseller"],
)
def test_non_managers_cannot_create_users(role_code, make_user, auth_client):
    user = make_user(role_code=role_code)
    client = auth_client(user)
    resp = client.post(USERS, _create_payload(), format="json")
    assert resp.status_code == 403


def test_laboratory_creates_technician(make_user, auth_client):
    lab = make_user(role_code="laboratory", email="lab@exemplo.com")
    client = auth_client(lab)
    resp = client.post(
        USERS,
        _create_payload(email="tecnico@exemplo.com", role_code="technician"),
        format="json",
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["role"]["code"] == "technician"
    # criado pode logar
    login = client.post(
        "/api/v1/auth/login",
        {"email": "tecnico@exemplo.com", "password": PASSWORD},
        format="json",
    )
    assert login.status_code == 200


def test_duplicated_email_is_rejected(make_user, auth_client):
    lab = make_user(role_code="laboratory", email="lab@exemplo.com")
    make_user(role_code="patient", email="existe@exemplo.com")
    client = auth_client(lab)
    resp = client.post(
        USERS, _create_payload(email="existe@exemplo.com"), format="json"
    )
    assert resp.status_code == 400


def test_patient_sees_own_record_but_not_others(make_user, auth_client):
    a = make_user(role_code="patient", email="a@exemplo.com")
    b = make_user(role_code="patient", email="b@exemplo.com")
    client_a = auth_client(a)
    assert client_a.get(f"{USERS}/{a.pk}").status_code == 200
    resp = client_a.get(f"{USERS}/{b.pk}")
    assert resp.status_code == 403


def test_seed_roles_is_idempotent(make_user, seeded_roles):
    make_user(role_code="patient")
    count_roles = Role.objects.count()
    count_perms = Permission.objects.count()
    call_command("seed_roles", verbosity=0)
    call_command("seed_roles", verbosity=0)
    assert Role.objects.count() == count_roles == 5
    assert Permission.objects.count() == count_perms == len(
        __import__("apps.accounts.rbac", fromlist=["PERMISSION_CATALOG"]).PERMISSION_CATALOG
    )
