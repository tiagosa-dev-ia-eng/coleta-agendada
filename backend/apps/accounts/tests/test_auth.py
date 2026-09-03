"""Testes de autenticação JWT, lockout e auditoria (doc 11; doc 14 §5)."""
from rest_framework.test import APIClient

from apps.audit.models import AuditLog

LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"
ME = "/api/v1/auth/me"
PASSWORD = "SenhaForte123!"


def _post(client, url, payload, **kw):
    return client.post(url, payload, format="json", **kw)


def test_login_success_returns_tokens_and_permissions(make_user):
    user = make_user(role_code="laboratory", first_name="Lab")
    client = APIClient()
    resp = _post(client, LOGIN, {"email": user.email, "password": PASSWORD})
    assert resp.status_code == 200
    body = resp.json()
    assert body["access"] and body["refresh"]
    assert body["user"]["role"]["code"] == "laboratory"
    assert "user.manage" in body["user"]["permissions"]
    assert body["user"]["name"] == "Lab"
    assert AuditLog.objects.filter(action="auth.login", entity_id=user.pk).exists()


def test_login_wrong_password_then_lockout(make_user):
    user = make_user(role_code="patient")
    client = APIClient()
    for _ in range(4):  # abaixo do limite (MAX_LOGIN_ATTEMPTS=5)
        resp = _post(client, LOGIN, {"email": user.email, "password": "errada1"})
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "invalid_credentials"
    # 5ª falha: bloqueia
    resp = _post(client, LOGIN, {"email": user.email, "password": "errada1"})
    assert resp.status_code == 423
    assert resp.json()["error"]["code"] == "account_locked"
    user.refresh_from_db()
    assert user.locked_until is not None
    assert AuditLog.objects.filter(action="auth.login_failed").count() == 5
    assert AuditLog.objects.filter(action="auth.account_locked", entity_id=user.pk).exists()
    # mesmo com a senha correta, continua bloqueado
    resp = _post(client, LOGIN, {"email": user.email, "password": PASSWORD})
    assert resp.status_code == 423


def test_login_success_resets_failed_attempts(make_user):
    user = make_user(role_code="patient")
    client = APIClient()
    _post(client, LOGIN, {"email": user.email, "password": "errada1"})
    _post(client, LOGIN, {"email": user.email, "password": "errada1"})
    ok = _post(client, LOGIN, {"email": user.email, "password": PASSWORD})
    assert ok.status_code == 200
    user.refresh_from_db()
    assert user.failed_login_attempts == 0
    assert user.locked_until is None


def test_login_unknown_email_is_generic(anon_client):
    resp = _post(anon_client, LOGIN, {"email": "naoexiste@x.com", "password": "x"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_credentials"


def test_me_returns_own_profile(make_user, auth_client):
    user = make_user(role_code="pharmacy", email="farmacia@exemplo.com")
    client = auth_client(user)
    resp = client.get(ME)
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "farmacia@exemplo.com"
    assert body["role"]["code"] == "pharmacy"
    assert body["permissions"]


def test_me_requires_authentication(anon_client):
    resp = anon_client.get(ME)
    assert resp.status_code == 401


def test_refresh_rotation_blacklists_old_token(make_user):
    user = make_user(role_code="technician")
    client = APIClient()
    login = _post(client, LOGIN, {"email": user.email, "password": PASSWORD}).json()
    old_refresh = login["refresh"]
    resp = _post(client, REFRESH, {"refresh": old_refresh})
    assert resp.status_code == 200
    assert resp.json()["access"]
    # rotação ativa: reutilizar o refresh antigo é rejeitado
    resp2 = _post(client, REFRESH, {"refresh": old_refresh})
    assert resp2.status_code == 401


def test_logout_blacklists_refresh(make_user):
    user = make_user(role_code="reseller")
    client = APIClient()
    login = _post(client, LOGIN, {"email": user.email, "password": PASSWORD}).json()
    refresh = login["refresh"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login['access']}")
    resp = client.post(LOGOUT, {"refresh": refresh}, format="json")
    assert resp.status_code == 204
    resp2 = client.post(REFRESH, {"refresh": refresh}, format="json")
    assert resp2.status_code == 401
