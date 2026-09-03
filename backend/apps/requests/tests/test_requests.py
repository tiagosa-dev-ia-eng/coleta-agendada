"""Testes M3 — solicitações, máquina de estados, histórico e pedido médico."""
import io
from datetime import date, timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.audit.models import AuditLog
from apps.patients.models import Patient
from apps.requests.models import CollectionRequest, RequestStatusHistory
from apps.requests.services import InvalidTransition, RequestStateService

PASSWORD = "SenhaForte123!"
REQUESTS = "/api/v1/requests"


def _auth_patient(make_user, auth_client, email="paciente-m3@exemplo.com"):
    u = make_user(role_code="patient", email=email)
    return u, auth_client(u)


def _create_request(client, **over):
    payload = {
        "desired_date": (date.today() + timedelta(days=5)).isoformat(),
        "desired_period": "morning",
        "collection_mode": "pharmacy",
        "preferred_location": "Farmácia Saúde",
    }
    payload.update(over)
    return client.post(REQUESTS, payload, format="json")


def test_patient_creates_request_with_protocol(make_user, auth_client):
    u, client = _auth_patient(make_user, auth_client)
    resp = _create_request(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["protocol"].startswith("CA-")
    assert body["status"] == "REQUESTED"
    assert body["patient"]["email"] == "paciente-m3@exemplo.com"
    # auto-provisiona perfil do paciente
    assert Patient.objects.filter(user=u).exists()
    # histórico inicial + auditoria
    assert RequestStatusHistory.objects.filter(request_id=body["id"]).count() == 1
    assert AuditLog.objects.filter(action="request.created").exists()


def test_non_patient_cannot_create(make_user, auth_client):
    u = make_user(role_code="laboratory", email="lab@x.com")
    resp = _create_request(auth_client(u))
    assert resp.status_code == 403


def test_patient_scopes_list_and_retrieve(make_user, auth_client):
    u1, c1 = _auth_patient(make_user, auth_client, email="a@exemplo.com")
    u2, c2 = _auth_patient(make_user, auth_client, email="b@exemplo.com")
    r1 = _create_request(c1).json()
    _create_request(c2)
    lst = c1.get(REQUESTS)
    assert lst.status_code == 200
    ids = [r["id"] for r in lst.json()]
    assert r1["id"] in ids and len(ids) == 1
    assert c1.get(f"{REQUESTS}/{r1['id']}").status_code == 200
    other = CollectionRequest.objects.exclude(pk=r1["id"]).first()
    assert c1.get(f"{REQUESTS}/{other.pk}").status_code == 403


def test_laboratory_lists_all(make_user, auth_client):
    u1, c1 = _auth_patient(make_user, auth_client, email="a2@exemplo.com")
    _create_request(c1)
    lab = make_user(role_code="laboratory", email="lab2@exemplo.com")
    resp = auth_client(lab).get(REQUESTS)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_requested_can_cancel_and_history_markup(make_user, auth_client):
    u, client = _auth_patient(make_user, auth_client)
    req_id = _create_request(client).json()["id"]
    resp = client.post(f"{REQUESTS}/{req_id}/cancel", {"reason": "desistiu"}, format="json")
    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELED"
    req = CollectionRequest.objects.get(pk=req_id)
    assert req.status == "CANCELED"
    hist = client.get(f"{REQUESTS}/{req_id}/history").json()
    assert [h["to_status"] for h in hist] == ["REQUESTED", "CANCELED"]
    assert AuditLog.objects.filter(action="request.status_changed").exists()


def test_invalid_transition_rejected(make_user, auth_client):
    u, client = _auth_patient(make_user, auth_client)
    req_id = _create_request(client).json()["id"]
    # paciente não deve conseguir pular direto para APPROVED via endpoint (não existe),
    # mas o serviço de domínio bloqueia: teste direto no serviço
    req = CollectionRequest.objects.get(pk=req_id)
    with pytest.raises(InvalidTransition):
        RequestStateService.transition(req, "APPROVED", changed_by=u, origin="user")


def test_cancel_terminal_rejected(make_user, auth_client):
    u, client = _auth_patient(make_user, auth_client)
    req_id = _create_request(client).json()["id"]
    req = CollectionRequest.objects.get(pk=req_id)
    RequestStateService.cancel(req, changed_by=u, origin="user")
    req.refresh_from_db()
    # CANCELED é terminal: segunda transição/cancelamento falha
    with pytest.raises(InvalidTransition):
        RequestStateService.transition(req, "QUOTE_DRAFT", changed_by=u, origin="user")


def test_upload_medical_order_pdf(make_user, auth_client):
    u, client = _auth_patient(make_user, auth_client)
    req_id = _create_request(client).json()["id"]
    f = SimpleUploadedFile(
        "pedido.pdf",
        io.BytesIO(b"%PDF-1.4 fake").read(),
        content_type="application/pdf",
    )
    resp = client.post(f"{REQUESTS}/{req_id}/medical-orders", {"file": f}, format="multipart")
    assert resp.status_code == 201
    assert resp.json()["mime_type"] == "application/pdf"
    assert resp.json()["size"] > 0
    assert AuditLog.objects.filter(action="medical_order.uploaded").exists()


def test_upload_rejects_bad_type_and_size(make_user, auth_client):
    u, client = _auth_patient(make_user, auth_client)
    req_id = _create_request(client).json()["id"]
    bad = SimpleUploadedFile("virus.txt", b"hello", content_type="text/plain")
    resp = client.post(f"{REQUESTS}/{req_id}/medical-orders", {"file": bad}, format="multipart")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "invalid_file"
    # tipo ok, tamanho acima do limite (10MB)
    big = SimpleUploadedFile(
        "grande.pdf", b"x" * (10 * 1024 * 1024 + 1), content_type="application/pdf"
    )
    resp = client.post(f"{REQUESTS}/{req_id}/medical-orders", {"file": big}, format="multipart")
    assert resp.status_code == 400


def test_medical_orders_only_for_scope(make_user, auth_client):
    u1, c1 = _auth_patient(make_user, auth_client, email="a3@exemplo.com")
    u2, c2 = _auth_patient(make_user, auth_client, email="b3@exemplo.com")
    req_id = _create_request(c1).json()["id"]
    f = SimpleUploadedFile("p.pdf", b"%PDF", content_type="application/pdf")
    c1.post(f"{REQUESTS}/{req_id}/medical-orders", {"file": f}, format="multipart")
    # outro paciente não vê anexos
    resp = c2.get(f"{REQUESTS}/{req_id}/medical-orders")
    assert resp.status_code == 403
