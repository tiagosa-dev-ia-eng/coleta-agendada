"""Provedor do canal WhatsApp (B-03 — Z-PRO/Dorislabs) — R-006.

Abstração de envio OUTBOUND. O webhook de entrada permanece o mesmo
(payload próprio: from/body/location/message_id). Provedor real é selecionado
por WHATSAPP_PROVIDER (default 'simulator'); o adapter Z-PRO é configurado por
env (ZPRO_BASE_URL/ZPRO_TOKEN/ZPRO_SEND_PATH) — endpoints e payload exatos
devem ser validados com a coleção Z-PRO (Postman) e as credenciais reais.
"""
import json
import logging
import os
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)


class ProviderError(RuntimeError):
    """Falha ao entregar mensagem no provedor WhatsApp."""


class SimulatorProvider:
    """Provedor de desenvolvimento: mensagens ficam só no banco (simulador)."""

    provider = "simulator"

    def deliver_outbound(self, message):
        return None


class ZProGateway:
    """Adapter Z-PRO (integração Dorislabs) para envio outbound."""

    provider = "zpro"

    def __init__(self):
        self.base_url = os.getenv("ZPRO_BASE_URL", "").rstrip("/")
        self.token = os.getenv("ZPRO_TOKEN", "")
        self.send_path = os.getenv("ZPRO_SEND_PATH", "")

    def deliver_outbound(self, message):
        if not (self.base_url and self.token and self.send_path):
            raise ProviderError(
                "Z-PRO não configurado: defina ZPRO_BASE_URL, ZPRO_TOKEN e "
                "ZPRO_SEND_PATH (coleção Z-PRO — validação pendente)."
            )
        url = f"{self.base_url}{self.send_path}"
        payload = {
            "to": message.conversation.phone,
            "message": message.content,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp.read()
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            raise ProviderError(f"Falha Z-PRO: {exc}") from exc
        return True


def get_provider():
    name = getattr(settings, "WHATSAPP_PROVIDER", "simulator")
    if name == "zpro":
        return ZProGateway()
    return SimulatorProvider()
