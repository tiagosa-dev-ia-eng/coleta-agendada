"""Testes D-01/D-03 — chatbot devolve o local de coleta (CollectionPoint) mais próximo.

O paciente envia a localização (payload location ou texto "lat, lon") e o
chatbot responde o CollectionPoint ativo mais próximo da rede — farmácia OU
laboratório — com horário de funcionamento e estado (aberto/fechado).
"""

import uuid
from decimal import Decimal

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.collection_points.geolocation import (
    haversine_km,
    nearest_collection_points,
    parse_coordinates,
)
from apps.collection_points.models import CollectionPoint
from apps.organizations.models import Laboratory, Pharmacy
from apps.whatsapp.models import WhatsAppConversation

WEBHOOK = "/api/v1/webhooks/whatsapp"
PHONE = "5511988880001"

REF_LAT, REF_LON = -23.5505, -46.6333  # centro de São Paulo (demo)


def _env(make_user):
    lab_u = make_user(role_code="laboratory", email="lab-d01@exemplo.com")
    lab = Laboratory.objects.create(name="Lab D-01", owner=lab_u)
    patient = make_user(role_code="patient", email="pac-d01@exemplo.com", phone=PHONE)
    return {"lab_user": lab_u, "lab": lab, "patient": patient}


def _add_pharmacy(make_user, lab, *, name="Farmácia Teste"):
    user = make_user(role_code="pharmacy", email=f"farm-{uuid.uuid4().hex[:8]}@exemplo.com")
    return Pharmacy.objects.create(user=user, laboratory=lab, name=name)


def _add_point(lab, *, name, lat, lon, kind="pharmacy", pharmacy=None, status="active"):
    return CollectionPoint.objects.create(
        laboratory=lab,
        kind=kind,
        pharmacy=pharmacy,
        name=name,
        address="Rua Exemplo, 100",
        city="São Paulo",
        state="SP",
        zip_code="01000-000",
        latitude=Decimal(str(lat)),
        longitude=Decimal(str(lon)),
        status=status,
    )


def _send(patient_user, body, message_id=None, **extra):
    client = APIClient()
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


def _last_outbound(conv):
    return conv.messages.filter(direction="outbound").order_by("-pk").first()


# ---------- geolocalização (módulo) ----------


def test_haversine_positive_and_symmetric():
    d = haversine_km(REF_LAT, REF_LON, REF_LAT + 0.01, REF_LON + 0.01)
    assert d > 0
    assert abs(d - haversine_km(REF_LAT + 0.01, REF_LON + 0.01, REF_LAT, REF_LON)) < 1e-9


def test_parse_coordinates_accepts_valid_pair_and_rejects_noise():
    assert parse_coordinates("minha localização é -23.5505, -46.6333") == (-23.5505, -46.6333)
    assert parse_coordinates("100, 200") is None
    assert parse_coordinates("às 10, 30") is None
    assert parse_coordinates("") is None
    assert parse_coordinates("não tenho localização") is None


def test_nearest_collection_points_orders_and_mixes_kinds(make_user):
    env = _env(make_user)
    pharmacy = _add_pharmacy(make_user, env["lab"], name="Farmácia Central")
    _add_point(
        env["lab"], name="Farmácia Longe", lat=REF_LAT - 0.2, lon=REF_LON - 0.2, pharmacy=pharmacy
    )
    _add_point(
        env["lab"],
        name="Laboratório Longe",
        lat=REF_LAT - 0.3,
        lon=REF_LON - 0.3,
        kind="laboratory",
    )
    pharmacy_near = _add_pharmacy(make_user, env["lab"], name="Farmácia Perto")
    _add_point(
        env["lab"],
        name="Farmácia Perto",
        lat=REF_LAT + 0.001,
        lon=REF_LON + 0.001,
        pharmacy=pharmacy_near,
    )
    inactive = _add_pharmacy(make_user, env["lab"], name="Farmácia Inativa")
    _add_point(
        env["lab"],
        name="Farmácia Inativa",
        lat=REF_LAT + 0.0005,
        lon=REF_LON + 0.0005,
        pharmacy=inactive,
        status="inactive",
    )
    ranked = nearest_collection_points(env["lab"].pk, REF_LAT, REF_LON, limit=5)
    assert ranked[0][2].name == "Farmácia Perto"
    assert ranked[0][0] < ranked[1][0]
    names = [point.name for _, _, point in ranked]
    kinds = {kind for _, kind, _ in ranked}
    assert "Farmácia Inativa" not in names
    assert "pharmacy" in kinds and "laboratory" in kinds
    assert len(ranked) == 3


# ---------- pipeline do chatbot (webhook) ----------


def test_structured_location_returns_nearest_with_schedule(make_user):
    env = _env(make_user)
    pharmacy = _add_pharmacy(make_user, env["lab"], name="Farmácia Central")
    _add_point(
        env["lab"],
        name="Farmácia Central",
        lat=REF_LAT + 0.001,
        lon=REF_LON + 0.001,
        pharmacy=pharmacy,
    )
    _add_point(
        env["lab"],
        name="Farmácia Longe",
        lat=REF_LAT - 0.2,
        lon=REF_LON - 0.2,
        pharmacy=_add_pharmacy(make_user, env["lab"], name="Longe"),
    )
    resp = _send(
        env["patient"],
        "",
        message_id=uuid.uuid4().hex,
        location={"latitude": REF_LAT, "longitude": REF_LON},
    )
    assert resp.status_code == 200
    conv = WhatsAppConversation.objects.get(phone=PHONE)
    reply = _last_outbound(conv).content
    assert "local de coleta" in reply
    assert "Farmácia Central" in reply
    assert "km" in reply
    assert "Horário" in reply
    assert "fechado no momento" in reply  # ponto nasce fechado (D-03)
    assert "Farmácia Longe" not in reply
    inbound = conv.messages.filter(direction="inbound").first()
    assert inbound.ai_interpretation["intent"] == "nearest_pharmacy"
    assert inbound.ai_used_mock is False


def test_laboratory_point_can_be_nearest(make_user):
    env = _env(make_user)
    _add_point(
        env["lab"],
        name="Laboratório Central",
        lat=REF_LAT + 0.001,
        lon=REF_LON + 0.001,
        kind="laboratory",
    )
    resp = _send(env["patient"], "", location={"latitude": REF_LAT, "longitude": REF_LON})
    assert resp.status_code == 200
    conv = WhatsAppConversation.objects.get(phone=PHONE)
    assert "o laboratório Laboratório Central" in _last_outbound(conv).content


def test_text_coordinates_returns_nearest_point(make_user):
    env = _env(make_user)
    pharmacy = _add_pharmacy(make_user, env["lab"], name="Farmácia Texto")
    _add_point(
        env["lab"],
        name="Farmácia Texto",
        lat=REF_LAT + 0.001,
        lon=REF_LON + 0.001,
        pharmacy=pharmacy,
    )
    resp = _send(env["patient"], f"{REF_LAT}, {REF_LON}")
    assert resp.status_code == 200
    conv = WhatsAppConversation.objects.get(phone=PHONE)
    assert "Farmácia Texto" in _last_outbound(conv).content


def test_nearest_ask_without_location_prompts_share(make_user):
    env = _env(make_user)
    resp = _send(env["patient"], "Qual o local de coleta mais próximo da minha localização?")
    assert resp.status_code == 200
    conv = WhatsAppConversation.objects.get(phone=PHONE)
    reply = _last_outbound(conv).content
    assert "Localização" in reply
    inbound = conv.messages.filter(direction="inbound").first()
    assert inbound.ai_interpretation["intent"] == "nearest_pharmacy"
    assert conv.status == "open"


def test_location_without_georeferenced_point_routes_to_human(make_user):
    env = _env(make_user)  # rede sem ponto com coordenada
    resp = _send(env["patient"], "", location={"latitude": REF_LAT, "longitude": REF_LON})
    assert resp.status_code == 200
    conv = WhatsAppConversation.objects.get(phone=PHONE)
    reply = _last_outbound(conv).content
    assert "atendente humano" in reply
    assert conv.status == "human"
    from apps.requests.models import CollectionRequest

    assert CollectionRequest.objects.count() == 0


def test_location_message_idempotent(make_user):
    env = _env(make_user)
    pharmacy = _add_pharmacy(make_user, env["lab"], name="Farmácia Única")
    _add_point(
        env["lab"],
        name="Farmácia Única",
        lat=REF_LAT + 0.001,
        lon=REF_LON + 0.001,
        pharmacy=pharmacy,
    )
    mid = uuid.uuid4().hex
    location = {"latitude": REF_LAT, "longitude": REF_LON}
    r1 = _send(env["patient"], "", message_id=mid, location=location)
    assert r1.status_code == 200
    conv = WhatsAppConversation.objects.get(phone=PHONE)
    count = conv.messages.count()
    r2 = _send(env["patient"], "", message_id=mid, location=location)
    assert r2.status_code == 200
    assert WhatsAppConversation.objects.get(phone=PHONE).messages.count() == count
