"""Testes D-01 — chatbot devolve a farmácia mais próxima da localização.

Demanda D-01 (docs/demandas.md): o paciente envia a localização (mensagem de
localização ou par \"latitude, longitude\" no texto) e o chatbot responde com
a farmácia mais próxima da rede do laboratório do canal.
"""
import uuid
from decimal import Decimal

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.organizations.geolocation import (
    haversine_km,
    nearest_collection_points,
    nearest_pharmacies,
    parse_coordinates,
)
from apps.organizations.models import Pharmacy
from apps.whatsapp.models import WhatsAppConversation

WEBHOOK = "/api/v1/webhooks/whatsapp"
PHONE = "5511988880001"

# Referência: centro de São Paulo (demo do simulador)
REF_LAT, REF_LON = -23.5505, -46.6333


def _env(make_user):
    from apps.organizations.models import Laboratory

    lab_u = make_user(role_code="laboratory", email="lab-d01@exemplo.com")
    lab = Laboratory.objects.create(name="Lab D-01", owner=lab_u)
    patient = make_user(role_code="patient", email="pac-d01@exemplo.com", phone=PHONE)
    return {"lab_user": lab_u, "lab": lab, "patient": patient}


def _add_pharmacy(make_user, lab, *, name, lat, lon, status="active"):
    """Cria usuário + perfil Pharmacy (user é OneToOne obrigatório)."""
    user = make_user(
        role_code="pharmacy",
        email=f"farm-{uuid.uuid4().hex[:8]}@exemplo.com",
    )
    return Pharmacy.objects.create(
        user=user,
        laboratory=lab,
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
    assert parse_coordinates("-23.5505,-46.6333") == (-23.5505, -46.6333)
    # valores fora da faixa -> rejeita
    assert parse_coordinates("100, 200") is None
    # frase comum com números sem decimal/sinal -> rejeita
    assert parse_coordinates("às 10, 30") is None
    assert parse_coordinates("") is None
    assert parse_coordinates("não tenho localização") is None


def test_nearest_pharmacies_orders_by_distance(make_user):
    env = _env(make_user)
    _add_pharmacy(
        make_user, env["lab"], name="Farmácia Longe", lat=REF_LAT - 0.2, lon=REF_LON - 0.2
    )
    _add_pharmacy(
        make_user, env["lab"], name="Farmácia Perto", lat=REF_LAT + 0.002, lon=REF_LON + 0.002
    )
    # inativa com coordenada não entra
    _add_pharmacy(
        make_user, env["lab"], name="Farmácia Inativa",
        lat=REF_LAT + 0.001, lon=REF_LON + 0.001, status="inactive",
    )
    ranked = nearest_pharmacies(env["lab"].pk, REF_LAT, REF_LON, limit=3)
    assert ranked[0][1].name == "Farmácia Perto"
    assert ranked[0][0] < ranked[1][0]
    names = [p.name for _, p in ranked]
    assert "Farmácia Inativa" not in names
    assert len(ranked) == 2


# ---------- pipeline do chatbot (webhook) ----------

def test_structured_location_returns_nearest_pharmacy(make_user):
    env = _env(make_user)
    _add_pharmacy(
        make_user, env["lab"], name="Farmácia Longe", lat=REF_LAT - 0.2, lon=REF_LON - 0.2
    )
    _add_pharmacy(
        make_user, env["lab"], name="Farmácia Central", lat=REF_LAT + 0.001, lon=REF_LON + 0.001
    )
    resp = _send(
        env["patient"],
        "",
        message_id=uuid.uuid4().hex,
        location={"latitude": REF_LAT, "longitude": REF_LON},
    )
    assert resp.status_code == 200
    conv = WhatsAppConversation.objects.get(phone=PHONE)
    reply = _last_outbound(conv)
    assert "local de coleta" in reply.content
    assert "Farmácia Central" in reply.content
    assert "km" in reply.content
    assert "Farmácia Longe" not in reply.content
    inbound = conv.messages.filter(direction="inbound").first()
    assert inbound.ai_interpretation["intent"] == "nearest_pharmacy"
    assert inbound.ai_used_mock is False  # caminho determinístico, sem LLM


def test_text_coordinates_returns_nearest_pharmacy(make_user):
    env = _env(make_user)
    _add_pharmacy(
        make_user, env["lab"], name="Farmácia Texto", lat=REF_LAT + 0.001, lon=REF_LON + 0.001
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
    assert conv.status == "open"  # não escala para humano: só pede localização


def test_location_without_georeferenced_pharmacy_routes_to_human(make_user):
    env = _env(make_user)  # laboratório sem farmácia com coordenada
    resp = _send(env["patient"], "", location={"latitude": REF_LAT, "longitude": REF_LON})
    assert resp.status_code == 200
    conv = WhatsAppConversation.objects.get(phone=PHONE)
    reply = _last_outbound(conv).content
    assert "atendente humano" in reply
    assert conv.status == "human"
    # nenhum efeito colateral de domínio (nenhuma solicitação criada)
    from apps.requests.models import CollectionRequest

    assert CollectionRequest.objects.count() == 0


def test_location_message_idempotent(make_user):
    env = _env(make_user)
    _add_pharmacy(
        make_user, env["lab"], name="Farmácia Única", lat=REF_LAT + 0.001, lon=REF_LON + 0.001
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


def test_laboratory_can_be_nearest_collection_point(make_user):
    """D-01: ponto de coleta = farmácia OU laboratório (decisão usuário)."""
    env = _env(make_user)
    lab = env["lab"]
    lab.address = "Av. Central, 1"
    lab.city = "São Paulo"
    lab.state = "SP"
    lab.latitude = Decimal(str(REF_LAT + 0.0005))
    lab.longitude = Decimal(str(REF_LON + 0.0005))
    lab.save()
    _add_pharmacy(
        make_user, lab, name="Farmácia Distante", lat=REF_LAT - 0.3, lon=REF_LON - 0.3
    )
    resp = _send(
        env["patient"], "", location={"latitude": REF_LAT, "longitude": REF_LON}
    )
    assert resp.status_code == 200
    conv = WhatsAppConversation.objects.get(phone=PHONE)
    reply = _last_outbound(conv).content
    assert "o laboratório Lab D-01" in reply
    assert "km" in reply
    assert "Farmácia Distante" not in reply


def test_nearest_collection_points_mixes_lab_and_pharmacy(make_user):
    """Ordem por proximidade inclui laboratório e farmácias da rede."""
    env = _env(make_user)
    lab = env["lab"]
    lab.latitude = Decimal(str(REF_LAT - 0.4))
    lab.longitude = Decimal(str(REF_LON - 0.4))
    lab.save()
    _add_pharmacy(make_user, lab, name="Farmácia Perto", lat=REF_LAT + 0.001, lon=REF_LON + 0.001)
    ranked = nearest_collection_points(lab.pk, REF_LAT, REF_LON, limit=3)
    assert ranked[0][1] == "pharmacy"
    assert ranked[0][2].name == "Farmácia Perto"
    assert ranked[0][0] < ranked[1][0]
    kinds = {kind for _, kind, _ in ranked}
    assert kinds == {"pharmacy", "laboratory"}
