"""Testes M4 — fluxo de orçamento e validação humana (RN-ORC / CT-INT-001/002/007)."""
from datetime import date, timedelta

from django.core.management import call_command

from apps.catalog.models import Exam
from apps.organizations.models import Laboratory


def _lab(make_user, name="Lab Orç"):
    u = make_user(role_code="laboratory", email="lab-orc@exemplo.com")
    lab = Laboratory.objects.create(name=name, owner=u)
    call_command("seed_catalog", verbosity=0)
    return u, lab


def _patient(make_user, auth_client, email="pac-orc@exemplo.com"):
    u = make_user(role_code="patient", email=email)
    client = auth_client(u)
    resp = client.post(
        "/api/v1/requests",
        {
            "desired_date": (date.today() + timedelta(days=3)).isoformat(),
            "desired_period": "morning",
            "collection_mode": "pharmacy",
        },
        format="json",
    )
    assert resp.status_code == 201, resp.content
    return u, client, resp.json()["id"]


def _draft(client_lab, req_id, items):
    return client_lab.post(
        f"/api/v1/requests/{req_id}/quotation-draft",
        {"items": items},
        format="json",
    )


def test_full_flow_draft_validate_send_approve(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    lab_client = auth_client(lab_user)
    patient, patient_client, req_id = _patient(make_user, auth_client)

    # 1) rascunho com preços do catálogo do laboratório
    resp = _draft(lab_client, req_id, [{"exam_code": "HEMO", "quantity": 1}, {"exam_code": "GLI"}])
    assert resp.status_code == 201, resp.content
    draft = resp.json()
    assert draft["quotation_type"] == "draft"
    assert draft["total"] == "53.00"  # 35 + 18
    assert draft["is_validated"] is False
    assert draft["request_protocol"].startswith("CA-")

    # 2) paciente não valida; laboratório valida (RN-ORC-002)
    assert patient_client.post(f"/api/v1/quotations/{draft['id']}/validate").status_code == 403
    val = lab_client.post(f"/api/v1/quotations/{draft['id']}/validate", format="json")
    assert val.status_code == 200, val.content
    final = val.json()
    assert final["quotation_type"] == "final"
    assert final["is_validated"] is True
    assert final["validated_by_email"] == "lab-orc@exemplo.com"
    assert final["version"] > draft["version"]

    # 3) envio e aprovação do paciente
    sent = lab_client.post(f"/api/v1/quotations/{final['id']}/send", format="json").json()
    assert sent["is_sent"] is True
    appr = patient_client.post(f"/api/v1/quotations/{final['id']}/approve", format="json")
    assert appr.status_code == 200
    # estados da solicitação percorridos
    history = patient_client.get(f"/api/v1/requests/{req_id}/history").json()
    states = [h["to_status"] for h in history]
    expected = ["REQUESTED", "QUOTE_DRAFT", "WAITING_HUMAN_VALIDATION", "QUOTE_SENT"]
    expected.append("APPROVED")
    assert states == expected


def test_send_without_validation_rejected(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    lab_client = auth_client(lab_user)
    _, _, req_id = _patient(make_user, auth_client)
    draft = _draft(lab_client, req_id, [{"exam_code": "HEMO"}]).json()
    resp = lab_client.post(f"/api/v1/quotations/{draft['id']}/send", format="json")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "quote_not_validated"


def test_validate_requires_all_priced(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    lab_client = auth_client(lab_user)
    _, _, req_id = _patient(make_user, auth_client)
    # exame existente sem preço no laboratório
    Exam.objects.create(code="SEMPRECO", name="Exame sem preço")
    resp = _draft(lab_client, req_id, [{"exam_code": "SEMPRECO"}])
    assert resp.status_code == 201
    assert resp.json()["missing_price_count"] == 1
    val = lab_client.post(f"/api/v1/quotations/{resp.json()['id']}/validate", format="json")
    assert val.status_code == 422
    assert val.json()["error"]["code"] == "quote_items_missing_price"


def test_reject_cancels_request(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    lab_client = auth_client(lab_user)
    patient, patient_client, req_id = _patient(make_user, auth_client)
    draft = _draft(lab_client, req_id, [{"exam_code": "HEMO"}]).json()
    final = lab_client.post(f"/api/v1/quotations/{draft['id']}/validate", format="json").json()
    lab_client.post(f"/api/v1/quotations/{final['id']}/send", format="json")
    resp = patient_client.post(
        f"/api/v1/quotations/{final['id']}/reject", {"reason": "caro"}, format="json"
    )
    assert resp.status_code == 200
    data = patient_client.get(f"/api/v1/requests/{req_id}").json()
    assert data["status"] == "CANCELED"


def test_patient_sees_only_own_quotations(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    lab_client = auth_client(lab_user)
    _, p1_client, req1 = _patient(make_user, auth_client, email="pa@exemplo.com")
    _, p2_client, req2 = _patient(make_user, auth_client, email="pb@exemplo.com")
    _draft(lab_client, req1, [{"exam_code": "HEMO"}])
    _draft(lab_client, req2, [{"exam_code": "GLI"}])
    assert p1_client.get(f"/api/v1/requests/{req1}/quotations").status_code == 200
    assert p1_client.get(f"/api/v1/requests/{req2}/quotations").status_code == 403
    lab_list = lab_client.get(f"/api/v1/requests/{req1}/quotations")
    assert lab_list.status_code == 200
    assert len(lab_list.json()) == 1


# ---------- B-05 / RN-ORC-004/005: revisão vira nova versão; aprovada imutável ----------

def test_revision_after_validation_creates_new_version(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    lab_client = auth_client(lab_user)
    _, _, req_id = _patient(make_user, auth_client, email="rev@exemplo.com")
    draft = _draft(lab_client, req_id, [{"exam_code": "HEMO"}]).json()
    final = lab_client.post(f"/api/v1/quotations/{draft['id']}/validate", format="json").json()
    assert (
        lab_client.get(f"/api/v1/requests/{req_id}").json()["status"]
        == "WAITING_HUMAN_VALIDATION"
    )
    # edição pós-validação: cria NOVA versão rascunho e volta a QUOTE_DRAFT
    revision = _draft(lab_client, req_id, [{"exam_code": "HEMO"}, {"exam_code": "GLI"}])
    assert revision.status_code == 201, revision.content
    body = revision.json()
    assert body["version"] > final["version"]
    assert body["quotation_type"] == "draft"
    assert lab_client.get(f"/api/v1/requests/{req_id}").json()["status"] == "QUOTE_DRAFT"
    # versão final validada anterior permanece imutável no histórico
    old = lab_client.get(f"/api/v1/quotations/{final['id']}").json()
    assert old["is_validated"] is True


def test_revision_after_send_allowed(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    lab_client = auth_client(lab_user)
    _, _, req_id = _patient(make_user, auth_client, email="rev2@exemplo.com")
    draft = _draft(lab_client, req_id, [{"exam_code": "HEMO"}]).json()
    final = lab_client.post(f"/api/v1/quotations/{draft['id']}/validate", format="json").json()
    lab_client.post(f"/api/v1/quotations/{final['id']}/send", format="json")
    # enviado (ainda não aprovado): revisão permitida (RN-ORC-004)
    rev = _draft(lab_client, req_id, [{"exam_code": "GLI"}])
    assert rev.status_code == 201, rev.content
    assert lab_client.get(f"/api/v1/requests/{req_id}").json()["status"] == "QUOTE_DRAFT"


def test_no_revision_after_approved(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    lab_client = auth_client(lab_user)
    patient, patient_client, req_id = _patient(make_user, auth_client, email="rev3@exemplo.com")
    draft = _draft(lab_client, req_id, [{"exam_code": "HEMO"}]).json()
    final = lab_client.post(f"/api/v1/quotations/{draft['id']}/validate", format="json").json()
    lab_client.post(f"/api/v1/quotations/{final['id']}/send", format="json")
    patient_client.post(f"/api/v1/quotations/{final['id']}/approve", format="json")
    assert lab_client.get(f"/api/v1/requests/{req_id}").json()["status"] == "APPROVED"
    blocked = _draft(lab_client, req_id, [{"exam_code": "HEMO"}])
    assert blocked.status_code == 409
    assert "RN-ORC-005" in blocked.json()["error"]["message"]


# ---------- B-05: validade do orçamento (15 dias) ----------

def test_expired_quotation_cannot_be_approved(make_user, auth_client):
    from datetime import timedelta as _td

    from django.utils import timezone as _tz

    lab_user, lab = _lab(make_user)
    lab_client = auth_client(lab_user)
    patient, patient_client, req_id = _patient(make_user, auth_client, email="exp@exemplo.com")
    draft = _draft(lab_client, req_id, [{"exam_code": "HEMO"}]).json()
    final = lab_client.post(f"/api/v1/quotations/{draft['id']}/validate", format="json").json()
    lab_client.post(f"/api/v1/quotations/{final['id']}/send", format="json")
    # envelhece a validação em 16 dias (B-05: validade 15)
    from apps.quotations.models import Quotation

    Quotation.objects.filter(pk=final["id"]).update(
        validated_at=_tz.now() - _td(days=16)
    )
    blocked = patient_client.post(f"/api/v1/quotations/{final['id']}/approve", format="json")
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "quote_expired"
    assert "15 dias" in blocked.json()["error"]["message"]
    # recusa/envio não são bloqueados pela expiração (apenas aprovação)
    assert lab_client.get(f"/api/v1/quotations/{final['id']}").json()["is_expired"] is True


def test_fresh_quotation_is_not_expired(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    lab_client = auth_client(lab_user)
    _, _, req_id = _patient(make_user, auth_client, email="fresh@exemplo.com")
    draft = _draft(lab_client, req_id, [{"exam_code": "HEMO"}]).json()
    final = lab_client.post(f"/api/v1/quotations/{draft['id']}/validate", format="json").json()
    body = lab_client.get(f"/api/v1/quotations/{final['id']}").json()
    assert body["is_expired"] is False
