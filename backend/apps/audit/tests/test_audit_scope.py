"""Testes — auditoria escopada por laboratório (v1.1.9)."""
from apps.audit.models import record as audit_record
from apps.organizations.models import Laboratory

BASE = "/api/v1/audit"


def _lab(make_user, email):
    u = make_user(role_code="laboratory", email=email)
    lab = Laboratory.objects.create(name=email.split("@")[0], owner=u)
    return u, lab


def test_laboratory_sees_only_own_audit(make_user, auth_client):
    user_a, lab_a = _lab(make_user, "lab-a@exemplo.com")
    user_b, lab_b = _lab(make_user, "lab-b@exemplo.com")
    audit_record(
        action="appointment.scheduled",
        entity_type="scheduling.Appointment",
        entity_id="1",
        user=user_a,
    )
    audit_record(
        action="payment.refunded",
        entity_type="payments.Payment",
        entity_id="2",
        user=user_b,
    )
    only_a = auth_client(user_a).get(BASE).json()
    assert only_a["count"] == 2
    assert len(only_a["items"]) == 1
    assert only_a["items"][0]["action"] == "appointment.scheduled"
    assert only_a["items"][0]["laboratory"]["id"] == lab_a.pk
    only_b = auth_client(user_b).get(BASE).json()
    assert [i["action"] for i in only_b["items"]] == ["payment.refunded"]


def test_superuser_sees_all(make_user, auth_client):
    user_a, _ = _lab(make_user, "lab-s1@exemplo.com")
    user_b, _ = _lab(make_user, "lab-s2@exemplo.com")
    audit_record(action="x.a", entity_type="T", entity_id="1", user=user_a)
    audit_record(action="y.b", entity_type="T", entity_id="2", user=user_b)
    sup = make_user(role_code="laboratory", email="sup-lab@exemplo.com")
    sup.is_superuser = True
    sup.save(update_fields=["is_superuser"])
    got = auth_client(sup).get(BASE).json()
    assert got["count"] == 2
    assert len(got["items"]) == 2


def test_patient_blocked(make_user, auth_client):
    patient = make_user(role_code="patient", email="pac-aud@exemplo.com")
    assert auth_client(patient).get(BASE).status_code == 403
