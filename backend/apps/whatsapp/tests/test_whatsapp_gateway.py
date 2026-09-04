"""Testes — provedor WhatsApp (B-03): simulador e Z-PRO (outbound)."""
import uuid

from django.test import override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.whatsapp.gateway import SimulatorProvider, ZProGateway
from apps.whatsapp.models import WhatsAppConversation

WEBHOOK = "/api/v1/webhooks/whatsapp"
PHONE = "5511988881234"


def _env(make_user):
    from apps.organizations.models import Laboratory

    lab_u = make_user(role_code="laboratory", email="lab-zpro@exemplo.com")
    lab = Laboratory.objects.create(name="Lab ZPro", owner=lab_u)
    p = make_user(role_code="patient", email="pac-zpro@exemplo.com", phone=PHONE)
    return lab_u, lab, p


def _send(patient_user, body):
    client = APIClient()
    token = str(RefreshToken.for_user(patient_user).access_token)
    client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
    return client.post(
        WEBHOOK,
        {
            "from": PHONE,
            "body": body,
            "message_id": uuid.uuid4().hex,
            "provider": "simulator",
        },
        format="json",
    )


def test_simulator_outbound_stays_in_db(make_user):
    lab_u, lab, patient = _env(make_user)
    resp = _send(patient, "Qual o status da minha solicitação?")
    assert resp.status_code == 200
    conv = WhatsAppConversation.objects.get(phone=PHONE)
    outbound = conv.messages.filter(direction="outbound").last()
    assert outbound is not None
    assert SimulatorProvider().provider == "simulator"


@override_settings(WHATSAPP_PROVIDER="zpro")
def test_zpro_unconfigured_logs_without_breaking(make_user):
    # sem ZPRO_* configurado: outbound registrado, erro registrado no log
    lab_u, lab, patient = _env(make_user)
    resp = _send(patient, "Oi, tudo bem?")
    assert resp.status_code == 200
    conv = WhatsAppConversation.objects.get(phone=PHONE)
    assert conv.messages.filter(direction="outbound").exists()


def test_zpro_deliver_builds_request(monkeypatch):
    monkeypatch.setenv("ZPRO_BASE_URL", "https://zpro.example")
    monkeypatch.setenv("ZPRO_TOKEN", "tok123")
    monkeypatch.setenv("ZPRO_SEND_PATH", "/message/send")
    captured = {}

    class FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return b'{}'

    def fake_post(req, timeout=None):
        captured["url"] = req.full_url
        captured["headers"] = req.headers
        return FakeResp()

    import apps.whatsapp.gateway as gw_mod

    monkeypatch.setattr(gw_mod.urllib.request, "urlopen", fake_post)
    gw = ZProGateway()
    from types import SimpleNamespace

    message = SimpleNamespace(
        conversation=SimpleNamespace(phone="5511999990000"),
        content="Olá!",
    )
    assert gw.deliver_outbound(message) is True
    assert captured["url"] == "https://zpro.example/message/send"
    assert captured["headers"]["Authorization"] == "Bearer tok123"
