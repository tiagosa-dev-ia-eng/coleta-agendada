"""Testes — consulta da trilha de auditoria (endpoint /audit)."""
from apps.audit.models import record as audit_record

BASE = "/api/v1/audit"


def _superuser(make_user):
    u = make_user(role_code="laboratory", email="aud-super@exemplo.com")
    u.is_superuser = True
    u.save(update_fields=["is_superuser"])
    return u


def test_superuser_lists_and_filters(make_user, auth_client):
    user = _superuser(make_user)
    patient = make_user(role_code="patient", email="pac-aud@exemplo.com")
    audit_record(
        action="requests.created",
        entity_type="requests.CollectionRequest",
        entity_id="CA-1",
        user=patient,
    )
    audit_record(
        action="payment.confirmed",
        entity_type="payments.Payment",
        entity_id="1",
        user=user,
    )
    client = auth_client(user)
    resp = client.get(BASE)
    assert resp.status_code == 200
    assert resp.json()["count"] == 2
    filtro = client.get(BASE, {"action": "payment.confirmed"})
    assert filtro.status_code == 200
    assert len(filtro.json()["items"]) == 1
    by_type = client.get(BASE, {"entity_type": "requests.CollectionRequest"})
    assert by_type.json()["count"] == 2
    assert len(by_type.json()["items"]) == 1


def test_non_superuser_blocked(make_user, auth_client):
    lab = make_user(role_code="laboratory", email="lab-aud@exemplo.com")
    resp = auth_client(lab).get(BASE)
    assert resp.status_code == 403
