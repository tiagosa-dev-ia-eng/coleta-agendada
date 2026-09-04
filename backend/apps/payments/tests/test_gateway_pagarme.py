"""Testes — gateway Pagar.me (B-01): adapter via OpenAPI Core v5."""
from types import SimpleNamespace

import pytest
from django.test import override_settings

from apps.payments.gateway import FakeGateway, GatewayError, PagarMeGateway, get_gateway


def _payment():
    return SimpleNamespace(
        code="PY-20260904-ABC123",
        amount="85.50",
        request=SimpleNamespace(
            patient=SimpleNamespace(user=SimpleNamespace(email="pac@exemplo.com"))
        ),
    )


def test_pagarme_create_link_builds_payload_and_url(monkeypatch):
    captured = {}

    def fake_post(self, url, payload):
        captured["url"] = url
        captured["payload"] = payload
        return {"id": "ord_999", "payment_url": "https://pay.pagar.me/xyz"}

    monkeypatch.setenv("PAGARME_SECRET_KEY", "sk_test_123")
    monkeypatch.setattr(PagarMeGateway, "_http_post", fake_post)
    gw = PagarMeGateway()
    result = gw.create_link(_payment())
    assert result["external_reference"] == "ord_999"
    assert result["url"] == "https://pay.pagar.me/xyz"
    assert result["gateway"] == "pagarme"
    assert captured["url"] == "https://api.pagar.me/core/v5/orders"
    assert captured["payload"]["amount"] == 8550  # centavos
    assert captured["payload"]["code"].startswith("PY-")


def test_pagarme_requires_secret(monkeypatch):
    monkeypatch.delenv("PAGARME_SECRET_KEY", raising=False)
    gw = PagarMeGateway()
    with pytest.raises(GatewayError):
        gw.create_link(_payment())


@override_settings(PAYMENT_GATEWAY="pagarme")
def test_registry_selects_pagarme(monkeypatch):
    monkeypatch.setenv("PAGARME_SECRET_KEY", "sk_test_456")
    gw = get_gateway()
    assert isinstance(gw, PagarMeGateway)
    assert gw.provider == "pagarme"


def test_fake_gateway_default():
    assert isinstance(get_gateway(), FakeGateway)
