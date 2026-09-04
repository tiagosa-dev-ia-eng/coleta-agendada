"""Testes — LGPD MVP (B-04): consentimento, exportação e anonimização."""

from apps.audit.models import AuditLog
from apps.patients.models import Patient

BASE = "/api/v1/patients/me"


def _patient_env(make_user, auth_client):
    u = make_user(role_code="patient", email="pac-lgpd@exemplo.com", phone="5511988880002")
    Patient.objects.create(user=u, birth_date="1990-05-10")
    return u, auth_client(u)


def test_consent_register_and_read(make_user, auth_client):
    u, client = _patient_env(make_user, auth_client)
    resp = client.post(f"{BASE}/consent", {"granted": False}, format="json")
    assert resp.status_code == 201
    assert resp.json()["granted"] is False
    got = client.get(f"{BASE}/consent").json()
    assert got["latest"]["granted"] is False
    assert AuditLog.objects.filter(action="patient.consent.updated").exists()


def test_data_export_and_consent_history(make_user, auth_client):
    u, client = _patient_env(make_user, auth_client)
    client.post(f"{BASE}/consent", {"granted": True}, format="json")
    data = client.get(f"{BASE}/export").json()
    assert data["usuario"]["email"] == "pac-lgpd@exemplo.com"
    assert data["consentimentos"][0]["granted"] is True
    assert AuditLog.objects.filter(action="patient.data_exported").exists()


def test_anonymize_requires_confirm_and_clears_pii(make_user, auth_client):
    u, client = _patient_env(make_user, auth_client)
    denied = client.post(f"{BASE}/anonymize", {}, format="json")
    assert denied.status_code == 400
    done = client.post(f"{BASE}/anonymize", {"confirm": "DELETE"}, format="json")
    assert done.status_code == 200
    u.refresh_from_db()
    assert u.is_active is False
    assert "@dados.invalid" in u.email
    assert "pac-lgpd@exemplo.com" not in u.email
    assert AuditLog.objects.filter(action="patient.anonymized").exists()


def test_non_patient_blocked(make_user, auth_client):
    lab = make_user(role_code="laboratory", email="lab-lgpd@exemplo.com")
    resp = auth_client(lab).get(f"{BASE}/export")
    assert resp.status_code == 403
