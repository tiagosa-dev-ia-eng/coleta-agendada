"""Cliente DeepSeek (ADR-005) — chamada via urllib (sem dependência extra)."""
import json
import logging
import os
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)


class AICallError(Exception):
    """Falha na chamada à API DeepSeek."""


SYSTEM_PROMPT = """Você é o assistente de inteligência artificial do Coleta Agendada,
uma plataforma de coletas de exames laboratoriais. Você recebe mensagens de
pacientes em linguagem natural e deve respondê-las APENAS com um JSON válido no
formato abaixo (nada além do JSON):

{
  "intent": "create_collection_request | check_status | help",
  "confidence": 0.0-1.0,
  "patient_data": {"name": "", "email": "", "phone": ""},
  "collection": {
    "mode": "pharmacy | domiciliary | laboratory",
    "desired_date": "AAAA-MM-DD (vazio se não citado)",
    "desired_period": "morning | afternoon | evening | vazio",
    "preferred_location": ""
  },
  "exams": [{"code": "código se reconhecível", "name": "nome do exame citado", "quantity": 1}],
  "medical_order": {"received": false},
  "missing_fields": ["data", "local", "exames"],
  "requires_human": false
}

REGRAS OBRIGATÓRIAS:
- Não invente exames: se não reconhecer um exame, preencha apenas "name" com o
  texto citado e NÃO invente "code".
- Não confirme preços, disponibilidade, pagamento nem conclusão de coleta.
- Se a mensagem pedir o andamento de uma solicitação e houver um protocolo
  (formato CA-AAAAAMMDD-XXXXXX), use intent "check_status" e ponha o protocolo
  em patient_data.name_ ignorado; melhor: campo "protocol" em collection.
- Se faltarem informações essenciais, marque em missing_fields e reduces a
  confiança.
- "requires_human": true quando houver ambiguidade relevante.
Exames conhecidos do catálogo disponíveis: %(catalog)s"""


def _build_user_message(text):
    return text


def call_deepseek(user_text, *, catalog_hint=""):
    """Chama a API DeepSeek e retorna o JSON bruto extraído."""
    api_key = getattr(settings, "DEEPSEEK_API_KEY", "") or os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise AICallError("DEEPSEEK_API_KEY não configurada (modo fallback).")
    base = getattr(settings, "DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    url = f"{base}/chat/completions"
    payload = {
        "model": getattr(settings, "DEEPSEEK_MODEL", "deepseek-chat"),
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT % {"catalog": catalog_hint or "não informado"}},
            {"role": "user", "content": user_text},
        ],
        "temperature": getattr(settings, "DEEPSEEK_TEMPERATURE", 0.2),
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode())
        content = body["choices"][0]["message"]["content"]
        return json.loads(content)
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, IndexError, json.JSONDecodeError) as exc:
        logger.warning("Falha na chamada DeepSeek: %s", exc)
        raise AICallError(str(exc)) from exc
