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
    # gate G-02: adicionar provedores reais aqui (ex.: Mercado Pago/Stripe), sem
    # mudar o domínio — apenas implementando PaymentGateway.
    raise ValueError(f"Gateway de pagamento desconhecido: {name}")
