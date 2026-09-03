"""Testes M6 — pagamentos (RF-014/015, doc 10, CT-INT-008)."""
from datetime import UTC, date, datetime, timedelta

from django.core.management import call_command

from apps.audit.models import AuditLog
from apps.organizations.models import Laboratory
from apps.payments.models import Payment, PaymentStatus


def _lab(make_user):
    u = make_user(role_code="laboratory", email="lab-pay@exemplo.com")
    lab = Laboratory.objects.create(name="Lab Pagamento", owner=u)
    call_command("seed_catalog", verbosity=0)
    return u, lab


def _approved_request(make_user, auth_client, lab_user, email="pac-pay@exemplo.com"):
    p = make_user(role_code="patient", email=email)
    pc = auth_client(p)
    lc = auth_client(lab_user)
    req_id = pc.post(
        "/api/v1/requests",
        {"desired_date": (date.today() + timedelta(days=3)).isoformat()},
        format="json",
    ).json()["id"]
    draft = lc.post(
        f"/api/v1/requests/{req_id}/quotation-draft",
        {"items": [{"exam_code": "HEMO"}]},
        format="json",
    ).json()
    final = lc.post(f"/api/v1/quotations/{draft['id']}/validate", format="json").json()
    lc.post(f"/api/v1/quotations/{final['id']}/send", format="json")
    pc.post(f"/api/v1/quotations/{final['id']}/approve", format="json")
    return p, pc, req_id, lc


def test_create_payment_link(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    _, pc, req_id, lc = _approved_request(make_user, auth_client, lab_user)
    resp = lc.post(f"/api/v1/requests/{req_id}/payments/link", {"amount": "100.00"}, format="json")
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["code"].startswith("PY-")
    assert body["status"] == "LINK_CREATED"
    assert "gateway.fake" in body["payment_url"]
    assert AuditLog.objects.filter(action="payment.link_created").exists()


def test_patient_cannot_create_link(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    p, pc, req_id, lc = _approved_request(make_user, auth_client, lab_user)
    resp = pc.post(f"/api/v1/requests/{req_id}/payments/link", {"amount": "10"}, format="json")
    assert resp.status_code == 403


def test_presential_and_manual_confirm(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    _, pc, req_id, lc = _approved_request(make_user, auth_client, lab_user)
    reg = lc.post(f"/api/v1/requests/{req_id}/payments", {"amount": "75.50"}, format="json")
    assert reg.status_code == 201
    assert reg.json()["status"] == "PENDING"
    pay_id = reg.json()["id"]
    conf = lc.post(f"/api/v1/payments/{pay_id}/confirm", format="json")
    assert conf.status_code == 200
    assert conf.json()["status"] == "CONFIRMED"
    assert conf.json()["paid_at"] is not None
    assert AuditLog.objects.filter(action="payment.confirmed").count() == 1


def test_webhook_confirm_idempotent(make_user, auth_client):
    """CT-INT-008: mensagem duplicada não duplica a operação."""
    lab_user, lab = _lab(make_user)
    _, _, req_id, lc = _approved_request(make_user, auth_client, lab_user)
    link = lc.post(
        f"/api/v1/requests/{req_id}/payments/link", {"amount": "50"}, format="json"
    )
    pay = link.json()
    ref = pay["external_reference"]
    anon = __import__("rest_framework.test", fromlist=["APIClient"]).APIClient()
    payload = {"external_reference": ref, "status": "confirmed"}
    first = anon.post("/api/v1/payments/webhook", payload, format="json")
    assert first.status_code == 200
    assert first.json()["status"] == "CONFIRMED"
    # duplicata: nada muda e não gera novo audit
    second = anon.post("/api/v1/payments/webhook", payload, format="json")
    assert second.status_code == 200
    assert second.json()["status"] == "CONFIRMED"
    assert AuditLog.objects.filter(action="payment.confirmed").count() == 1
    assert Payment.objects.get(pk=pay["id"]).paid_at is not None


def test_webhook_unknown_reference(make_user, auth_client):
    anon = __import__("rest_framework.test", fromlist=["APIClient"]).APIClient()
    resp = anon.post(
        "/api/v1/payments/webhook",
        {"external_reference": "PY-NADA", "status": "confirmed"},
        format="json",
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "payment_not_found"


def test_webhook_failed_event(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    _, _, req_id, lc = _approved_request(make_user, auth_client, lab_user)
    link = lc.post(
        f"/api/v1/requests/{req_id}/payments/link", {"amount": "50"}, format="json"
    )
    pay = link.json()
    anon = __import__("rest_framework.test", fromlist=["APIClient"]).APIClient()
    resp = anon.post(
        "/api/v1/payments/webhook",
        {"external_reference": pay["external_reference"], "status": "failed"},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "FAILED"


def test_payment_does_not_block_completion(make_user, auth_client):
    """Pagamento pendente + coleta concluída continuam válidos (ADR-008)."""
    lab_user, lab = _lab(make_user)
    tech_user = make_user(role_code="technician", email="tec-pay@exemplo.com")
    from apps.technicians.models import Technician

    tech = Technician.objects.create(user=tech_user, laboratory=lab)
    p, pc, req_id, lc = _approved_request(make_user, auth_client, lab_user)
    # link pendente criado antes da coleta
    pay = lc.post(f"/api/v1/requests/{req_id}/payments/link", {"amount": "42"}, format="json")
    assert pay.status_code == 201
    # agenda e conclui (sem exigir pagamento)
    appt = lc.post(
        f"/api/v1/requests/{req_id}/appointment",
        {
            "mode": "domiciliary",
            "scheduled_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            "technician_id": tech.pk,
        },
        format="json",
    ).json()
    tclient = auth_client(tech_user)
    tclient.post(f"/api/v1/appointments/{appt['id']}/check-in")
    done = tclient.post(f"/api/v1/appointments/{appt['id']}/complete").json()
    assert done["status"] == "COMPLETED"
    # pagamento segue pendente (LINK_CREATED) e não foi forçado
    assert Payment.objects.get(pk=pay.json()["id"]).status == PaymentStatus.LINK_CREATED
