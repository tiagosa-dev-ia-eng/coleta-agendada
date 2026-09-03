"""Validação da saída estruturada da IA (doc 08 §5 e §segurança).

Saída do LLM é ENTRADA NÃO CONFIÁVEL: validar via schema antes de persistir
(regra 11 do AGENTS.md).
"""
import datetime as _dt


class ExtractionError(ValueError):
    pass


INTENTS = {"create_collection_request", "check_status", "help"}
MODES = {"pharmacy", "domiciliary", "laboratory"}
PERIODS = {"morning", "afternoon", "evening"}


def _text(obj, key, default=""):
    value = (obj.get(key) or default) if isinstance(obj, dict) else default
    return str(value).strip()


def _as_date(value, default=None):
    if isinstance(value, str) and value:
        try:
            return _dt.date.fromisoformat(value).isoformat()
        except ValueError:
            return default
    return default


def normalize_extraction(raw, *, default_intent="help"):
    """Normaliza e valida o JSON da IA (doc 08 §5)."""

    if not isinstance(raw, dict):
        raise ExtractionError("Resposta da IA não é um objeto JSON.")

    intent = str(raw.get("intent") or default_intent)
    if intent not in INTENTS:
        intent = "help"

    try:
        confidence = float(raw.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    collection = raw.get("collection") or {}
    if not isinstance(collection, dict):
        collection = {}

    mode = str(collection.get("mode") or "pharmacy")
    if mode not in MODES:
        mode = "pharmacy"
    period = str(collection.get("desired_period") or "")
    if period not in PERIODS:
        period = ""
    desired_date = _as_date(collection.get("desired_date"))

    exams = raw.get("exams") or []
    if not isinstance(exams, list):
        exams = []

    clean_exams = []
    for ex in exams:
        if isinstance(ex, dict) and (ex.get("code") or ex.get("name")):
            clean_exams.append(
                {
                    "code": str(ex.get("code") or "").strip(),
                    "name": str(ex.get("name") or "").strip(),
                    "quantity": max(1, int(ex.get("quantity") or 1)),
                }
            )

    patient = raw.get("patient_data") or {}
    if not isinstance(patient, dict):
        patient = {}

    medical_order = raw.get("medical_order") or {}
    if isinstance(medical_order, bool):
        medical_order = {"received": medical_order}
    if not isinstance(medical_order, dict):
        medical_order = {}

    missing = raw.get("missing_fields") or []
    if not isinstance(missing, list):
        missing = [str(missing)]

    requires_human = bool(raw.get("requires_human", False))

    return {
        "intent": intent,
        "protocol": str(raw.get("protocol") or collection.get("protocol") or "").strip().upper(),
        "confidence": confidence,
        "patient_data": {
            "name": _text(patient, "name"),
            "email": _text(patient, "email").lower(),
            "phone": _text(patient, "phone"),
        },
        "collection": {
            "mode": mode,
            "desired_date": desired_date,
            "desired_period": period,
            "preferred_location": _text(collection, "preferred_location"),
        },
        "exams": clean_exams,
        "medical_order": {"received": bool(medical_order.get("received"))},
        "missing_fields": missing,
        "requires_human": requires_human,
    }
