"""IA simulada (fallback) — usada quando DEEPSEEK_API_KEY não está configurada
ou a API falha. Permite homologar o pipeline sem custo/credenciais.
"""
import datetime as _dt
import re

from apps.catalog.models import Exam

_PROTOCOL_RE = re.compile(r"CA-\d{8}-[A-F0-9]{6}", re.IGNORECASE)


def _today(days=0):
    return (_dt.date.today() + _dt.timedelta(days=days)).isoformat()


def mock_analyze(text):
    lower = text.lower()
    catalog = {e.code: e.name for e in Exam.objects.filter(active=True)}
    exams = []
    for code, name in catalog.items():
        if code.lower() in lower or name.lower().split()[0] in lower:
            exams.append({"code": code, "name": name, "quantity": 1})
    if not exams:
        # tenta capturar menções de exame com mais de uma palavra antes de 'amanhã'/'hoje'
        mention = re.search(r"(?:exame|exames|coleta|fazer)[s\s:]*([\w\u00C0-\u00FF ]+?)(?:\s(?:amanhã|hoje|de manhã|à tarde|à noite)|$)", lower)
        if mention:
            exams.append({"code": "", "name": mention.group(1).strip().title(), "quantity": 1})

    protocol = _PROTOCOL_RE.search(text)
    if protocol:
        return {
            "intent": "check_status",
            "confidence": 0.95,
            "protocol": protocol.group(0).upper(),
            "collection": {},
            "exams": [],
            "missing_fields": [],
            "requires_human": False,
        }
    if any(k in lower for k in ["solicitar", "quero fazer", "marcar", "agendar", "coleta", "exame", "exames", "fazer exame"]):
        mode = "pharmacy"
        if any(k in lower for k in ["domicílio", "domiciliar", "casa"]):
            mode = "domiciliary"
        elif any(k in lower for k in ["laboratório", "laboratorio", "unidade"]):
            mode = "laboratory"
        period = ""
        if any(k in lower for k in ["manhã", "manha", "cedo"]):
            period = "morning"
        elif "tarde" in lower:
            period = "afternoon"
        elif any(k in lower for k in ["noite", "noitinha"]):
            period = "evening"
        desired = ""
        if "amanhã" in lower or "amanha" in lower:
            desired = _today(1)
        elif "hoje" in lower:
            desired = _today(0)
        location = ""
        if "farmácia" in lower:
            location = "farmácia preferida pelo paciente"
        missing = []
        if not exams:
            missing.append("exames")
        if not desired:
            missing.append("data")
        requires_human = bool(missing) and len(exams) == 0
        confidence = 0.85 if exams else (0.5 if requires_human else 0.7)
        return {
            "intent": "create_collection_request",
            "confidence": confidence,
            "collection": {
                "mode": mode,
                "desired_date": desired,
                "desired_period": period,
                "preferred_location": location,
            },
            "exams": exams,
            "missing_fields": missing,
            "requires_human": requires_human,
            "medical_order": {"received": False},
        }
    return {"intent": "help", "confidence": 0.4, "collection": {}, "exams": [], "missing_fields": [], "requires_human": False}


def catalog_hint():
    names = Exam.objects.filter(active=True).values_list("code", "name")
    return "; ".join(f"{c} = {n}" for c, n in names[:40])
