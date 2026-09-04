"""Testes — economia de tokens no chatbot (DEEPSEEK_MOCK e rotas sem IA).

Decisão usuário 04/09/2026: validar respostas não deve gastar tokens.
- DEEPSEEK_MOCK=1 força o mock mesmo com chave (nenhuma chamada à API).
- Mensagem com protocolo (consulta de andamento) é resolvida sem IA.
"""
import uuid

from django.test import override_settings

from apps.patients.models import Patient
from apps.requests.models import CollectionRequest
from apps.whatsapp.models import WhatsAppConversation
from apps.whatsapp.services import WhatsAppService

WEBHOOK = "/api/v1/webhooks/whatsapp"
PHONE = "5511988885555"


def _env(make_user):
    from apps.organizations.models import Laboratory

    lab_u = make_user(role_code="laboratory", email="lab-tk@exemplo.com")
    lab = Laboratory.objects.create(name="Lab Tokens", owner=lab_u)
    p = make_user(role_code="patient", email="pac-tk@exemplo.com", phone=PHONE)
    patient = Patient.objects.create(user=p)
    return {"lab": lab, "patient": patient, "lab_user": lab_u}


def _send(patient_user, body, **extra):
    from rest_framework.test import APIClient
    from rest_framework_simplejwt.tokens import RefreshToken

    client = APIClient()
    token = str(RefreshToken.for_user(patient_user).access_token)
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    payload = {
        "from": PHONE,
        "body": body,
        "message_id": uuid.uuid4().hex,
        "provider": "simulator",
    }
    payload.update(extra)
    return client.post(WEBHOOK, payload, format="json")


def _inbound(conv):
    return conv.messages.filter(direction="inbound").first()


def test_protocol_inquiry_is_deterministic_no_ai(make_user):
    env = _env(make_user)
    req = CollectionRequest.objects.create(
        patient=env["patient"],
        laboratory=env["lab"],
        protocol="CA-20260904-ABCDEF",
        status="SCHEDULED",
    )
    resp = _send(
        env["patient"].user, f"qual o status da solicitação {req.protocol}?"
    )
    assert resp.status_code == 200
    conv = WhatsAppConversation.objects.get(phone=PHONE)
    inbound = _inbound(conv)
    assert inbound.ai_interpretation["intent"] == "check_status"
    assert inbound.ai_interpretation["protocol"] == req.protocol
    assert inbound.ai_used_mock is False  # nenhuma chamada de IA
    assert inbound.ai_model == ""
    outbound = conv.messages.filter(direction="outbound").last()
    assert req.protocol in outbound.content


@override_settings(DEEPSEEK_API_KEY="fake-key", DEEPSEEK_MOCK=True)
def test_deepseek_mock_avoids_api_call(monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("call_deepseek não deveria ser invocado com mock forçado")

    import apps.whatsapp.services as services

    monkeypatch.setattr(services, "call_deepseek", _boom)
    extraction, model, used_mock, ai_error = WhatsAppService.analyze(
        "Quero agendar hemograma amanhã"
    )
    assert used_mock is True
    assert model == "mock"
    assert extraction["intent"] == "create_collection_request"
