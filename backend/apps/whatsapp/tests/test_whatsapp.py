"""Testes M8 — webhook WhatsApp + IA (doc 08): idempotência, fluxo e proibições."""
import uuid

from django.core.management import call_command
from rest_framework.test import APIClient

from apps.patients.models import Patient
from apps.quotations.models import Quotation, QuotationType
from apps.requests.models import CollectionRequest
from apps.whatsapp.models import WhatsAppConversation

WEBHOOK = "/api/v1/webhooks/whatsapp"
PHONE = "5511988887777"


def _env(make_user):
    lab_u = make_user(role_code="laboratory", email="lab-wa@exemplo.com")
    from apps.organizations.models import Laboratory

    lab = Laboratory.objects.create(name="Lab WhatsApp", owner=lab_u)
    call_command("seed_catalog", verbosity=0)
    p = make_user(role_code="patient", email="pac-wa@exemplo.com", phone=PHONE)
    patient = Patient.objects.create(user=p)
    return {"lab_user": lab_u, "lab": lab, "patient": p, "patient_profile": patient}


def _send(patient_user, body, message_id=None, **extra):
    client = APIClient()
    from rest_framework_simplejwt.tokens import RefreshToken

    token = str(RefreshToken.for_user(patient_user).access_token)
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "from": PHONE,
        "body": body,
        "message_id": message_id or uuid.uuid4().hex,
        "provider": "simulator",
    }
    payload.update(extra)
    return client.post(WEBHOOK, payload, format="json")


def _messages(conv):
    return list(conv.messages.order_by("created_at").values_list("content", flat=True))


def test_create_request_and_draft_via_ia(make_user):
    env = _env(make_user)
    resp = _send(env["patient"], "Quero agendar coleta de hemograma amanhã de manhã")
    assert resp.status_code == 200
    conv = WhatsAppConversation.objects.get(phone=PHONE)
    msgs = _messages(conv)
    assert len(msgs) == 2  # inbound + outbound
    out = msgs[1]
    assert "Protocolo" in out and "CA-" in out
    req = CollectionRequest.objects.get(patient=env["patient_profile"])
    assert req.status == "QUOTE_DRAFT"
    assert req.status_history.filter(origin="whatsapp").exists()
    # rascunho IA existe; orçamento FINAL NUNCA é criado pelo pipeline (regra 12)
    draft = Quotation.objects.get(request=req)
    assert draft.generated_by_ai is True
    assert draft.quotation_type == QuotationType.DRAFT
    assert Quotation.objects.filter(request=req, quotation_type=QuotationType.FINAL).count() == 0
    # interpretação persistida com modelo/mock
    inbound = conv.messages.filter(direction="inbound").first()
    assert inbound.ai_interpretation["intent"] == "create_collection_request"
    assert inbound.ai_used_mock is True  # sem chave DeepSeek nos testes


def test_webhook_idempotent_on_duplicate(make_user):
    env = _env(make_user)
    mid = uuid.uuid4().hex
    resp1 = _send(env["patient"], "Quero agendar hemograma", message_id=mid)
    assert resp1.status_code == 200
    count_req = CollectionRequest.objects.count()
    count_msgs = WhatsAppConversation.objects.get(phone=PHONE).messages.count()
    resp2 = _send(env["patient"], "Quero agendar hemograma", message_id=mid)
    assert resp2.status_code == 200
    assert CollectionRequest.objects.count() == count_req  # não duplicou
    assert WhatsAppConversation.objects.get(phone=PHONE).messages.count() == count_msgs


def test_unknown_message_help_without_side_effect(make_user):
    env = _env(make_user)
    resp = _send(env["patient"], "Oi, tudo bem?")
    assert resp.status_code == 200
    conv = WhatsAppConversation.objects.get(phone=PHONE)
    # confiança baixa -> encaminhada a humano (sem efeito colateral de domínio)
    assert "atendente humano" in _messages(conv)[1]
    assert conv.status == "human"
    assert CollectionRequest.objects.count() == 0


def test_status_inquiry(make_user):
    env = _env(make_user)
    _send(env["patient"], "Quero agendar coleta de hemograma amanhã de manhã")
    req = CollectionRequest.objects.get(patient=env["patient_profile"])
    resp = _send(env["patient"], f"qual o status da solicitação {req.protocol}?")
    assert resp.status_code == 200
    conv = WhatsAppConversation.objects.get(phone=PHONE)
    assert req.protocol in _messages(conv)[-1]


def test_conversation_scope(make_user, auth_client):
    env = _env(make_user)
    _send(env["patient"], "Quero agendar coleta de hemograma")
    lab_client = auth_client(env["lab_user"])
    got = lab_client.get(f"/api/v1/whatsapp/conversations/by-phone/{PHONE}")
    assert got.status_code == 200
    assert len(got.json()["messages"]) == 2
    # outro paciente não acessa a conversa
    other = make_user(role_code="patient", email="outro@exemplo.com", phone="5599888777")
    Patient.objects.create(user=other)
    blocked = auth_client(other).get(f"/api/v1/whatsapp/conversations/by-phone/{PHONE}")
    assert blocked.status_code == 403
