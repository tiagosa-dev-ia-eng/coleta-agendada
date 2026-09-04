"""Adapter de gateway de pagamento (R-006 — integrações desacopladas).

Padrão: interface PaymentGateway; a implementação é escolhida por env
(PAYMENT_GATEWAY). No MVP roda o FakeGateway; um gateway real (G-02) implementa
a mesma interface (create_link/...) sem tocar no domínio.
"""
from django.conf import settings


class PaymentGateway:
    """Interface base do provedor de pagamento (doc 15 §3 — financeiro)."""

    provider = "base"

    def create_link(self, payment) -> dict:
        """Cria um link de pagamento para o Payment. Retorna {url, external_reference}."""
        raise NotImplementedError


class FakeGateway(PaymentGateway):
    """Gateway de desenvolvimento: devolve um link simbólico (G-02 no roadmap)."""

    provider = "fake"

    def create_link(self, payment) -> dict:
        url = f"https://gateway.fake/pay/{payment.code}"
        return {"url": url, "external_reference": payment.code}


def get_gateway() -> PaymentGateway:
    name = getattr(settings, "PAYMENT_GATEWAY", "fake")
    if name == "fake":
        return FakeGateway()
    if name == "pagarme":
        return PagarMeGateway()
    # integrações reais (B-01): implementar PaymentGateway e registrar aqui
    raise ValueError(f"Gateway de pagamento desconhecido: {name}")


class GatewayError(RuntimeError):
    """Falha na chamada ao gateway de pagamento."""


class PagarMeGateway(PaymentGateway):
    """Adapter Pagar.me Core (v5) — B-01 (docs.pagar.me, OpenAPI oficial).

    Autenticação: HTTP Basic com PAGARME_SECRET_KEY como usuário e senha vazia
    (conforme OpenAPI Pagar.me Core v5). Criação de pedido em POST {base}/orders
    (base default https://api.pagar.me/core/v5, configurável via env) — a forma
    exata do link de pagamento/checkout deve ser validada com a conta sandbox
    (chaves não existem nesta máquina; testes usam resposta simulada).
    """

    provider = "pagarme"

    def __init__(self):
        import os

        self.secret_key = os.getenv("PAGARME_SECRET_KEY", "")
        self.base_url = os.getenv("PAGARME_BASE_URL", "https://api.pagar.me/core/v5").rstrip("/")
        self.orders_path = os.getenv("PAGARME_ORDERS_PATH", "/orders")

    def _http_post(self, url, payload):
        import base64
        import json
        import urllib.error
        import urllib.request

        if not self.secret_key:
            raise GatewayError(
                "PAGARME_SECRET_KEY não configurada (gateway Pagar.me)."
            )
        token = base64.b64encode(f"{self.secret_key}:".encode()).decode()
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Basic {token}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            raise GatewayError(f"Falha no Pagar.me: {exc}") from exc

    def create_link(self, payment) -> dict:
        from decimal import Decimal

        amount_cents = int((Decimal(str(payment.amount)) * 100).to_integral_value())
        payload = {
            "code": payment.code,
            "amount": amount_cents,
            "items": [{"amount": amount_cents, "quantity": 1}],
        }
        customer_email = None
        if payment.request.patient.user.email:
            customer_email = payment.request.patient.user.email
        if customer_email:
            payload["customer"] = {"email": customer_email}
        data = self._http_post(self.base_url + self.orders_path, payload)
        order_id = str(data.get("id") or payment.code)
        # O link efetivo depende da configuração de checkout da conta; preservamos
        # a referência do pedido para o webhook (idempotência por external_reference).
        url = str(data.get("payment_url") or data.get("checkout_url") or "")
        return {"url": url, "external_reference": order_id, "gateway": self.provider}
