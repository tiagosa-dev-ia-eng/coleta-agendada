"""Pipeline WhatsApp + IA (doc 08) — webhook próprio idempotente.

Proibições garantidas neste pipeline (regra 12 do AGENTS.md): a IA NUNCA envia
orçamento final, não confirma preço/pagamento/disponibilidade/coleta. O fluxo
cria solicitação + RASCUNHO gerado por IA; a validação humana (M4) é obrigatória
antes de qualquer orçamento final.
"""
import logging
import re
import uuid

from django.conf import settings

from apps.ai.client import AICallError, call_deepseek
from apps.ai.mock import catalog_hint, mock_analyze
from apps.ai.schema import ExtractionError, normalize_extraction
from apps.audit.models import record as audit_record
from apps.collection_points import services as point_services
from apps.collection_points.geolocation import (
    nearest_collection_points,
    parse_coordinates,
    valid_coordinates,
)
from apps.whatsapp.models import Direction, WhatsAppConversation, WhatsAppMessage
from apps.whatsapp.validators import normalize_phone_digits

logger = logging.getLogger(__name__)

# Demanda D-01: texto do paciente pedindo o local de coleta mais próximo SEM
# localização ainda — o chatbot deve pedir para compartilhar a localização.
# O "local de coleta" do domínio é hoje a farmácia/ponto de coleta da rede
# (doc 06; Pharmacy é documentada como "Farmácia/ponto de coleta").
COLLECTION_TERM_MARKERS = (
    "farm",
    "local de coleta",
    "local de colet",
    "ponto de coleta",
    "ponto de colet",
)
PROXIMITY_MARKERS = (
    "próxim",
    "proxim",
    "mais próxima",
    "mais proxima",
    "mais perto",
    "perto",
    "onde fica",
    "localiza",
)

PROTOCOL_RE = re.compile(r"CA-\d{8}-[A-F0-9]{6}", re.IGNORECASE)


def normalize_phone(value):
    return normalize_phone_digits(value)


def _first_lab():
    from apps.organizations.models import Laboratory

    return Laboratory.objects.order_by("pk").first()


class WhatsAppService:
    @staticmethod
    def analyze(text):
        """Chama DeepSeek real (se chave) ou mock; normaliza a extração."""
        used_mock = False
        ai_error = False
        model = settings.DEEPSEEK_MODEL
        raw = None
        # DEEPSEEK_MOCK: validação/respostas SEM gasto de token (mesmo com chave)
        if settings.DEEPSEEK_MOCK or not settings.DEEPSEEK_API_KEY:
            used_mock = True
            model = "mock"
            raw = mock_analyze(text)
        else:
            try:
                raw = call_deepseek(text, catalog_hint=catalog_hint())
            except AICallError:
                used_mock = True
                ai_error = True
                raw = mock_analyze(text)
                model = "mock"
        try:
            return normalize_extraction(raw), model, used_mock, ai_error
        except ExtractionError:
            raise

    @staticmethod
    def _resolve_patient(phone, request_user):
        from apps.patients.models import Patient

        if request_user is not None and request_user.is_authenticated:
            prof = getattr(request_user, "patient_profile", None)
            if prof is not None:
                return prof
        return (
            Patient.objects.filter(user__phone__iexact=phone).first()
            or Patient.objects.filter(user__email=request_user.email).first()
            if request_user is not None and request_user.is_authenticated
            else Patient.objects.filter(user__phone__iexact=phone).first()
        )

    @staticmethod
    def _extract_coordinates(payload):
        """Localização estruturada (location) ou par \"lat, lon\" no texto."""
        loc = payload.get("location") or {}
        if isinstance(loc, dict):
            lat = loc.get("latitude", loc.get("lat"))
            lon = loc.get("longitude", loc.get("lon"))
            if lat is not None and lon is not None and valid_coordinates(lat, lon):
                return (float(lat), float(lon))
        return parse_coordinates(payload.get("body"))

    @staticmethod
    def _looks_like_nearest_pharmacy_ask(text):
        """Paciente pergunta pelo local de coleta mais próximo sem enviar localização.

        Exige um termo de ponto de coleta (farmácia/ponto/local de coleta) E um
        marcador de proximidade — evita capturar pedidos comuns de agendamento
        ("quero coleta na farmácia", "fazer coleta no ponto X").
        """
        lowered = (text or "").lower()
        has_term = any(marker in lowered for marker in COLLECTION_TERM_MARKERS)
        has_proximity = any(marker in lowered for marker in PROXIMITY_MARKERS)
        return has_term and has_proximity

    @staticmethod
    def _fmt_km(distance_km):
        if distance_km < 10:
            return f"{distance_km:.1f}".rstrip("0").rstrip(".")
        return f"{distance_km:.0f}"

    @staticmethod
    def handle_inbound(payload, *, request=None):
        phone = normalize_phone(payload.get("from"))
        text = str(payload.get("body") or "").strip()
        message_id = str(payload.get("message_id") or uuid.uuid4().hex)
        coords = WhatsAppService._extract_coordinates(payload)
        if not phone or (not text and coords is None):
            raise ValueError("from e body (ou location) são obrigatórios.")
        request_user = getattr(request, "user", None) if request else None
        provider = payload.get("provider") or settings.WHATSAPP_PROVIDER

        conv, _ = WhatsAppConversation.objects.get_or_create(
            phone=phone, defaults={"provider": provider, "laboratory": _first_lab()}
        )
        patient = WhatsAppService._resolve_patient(phone, request_user)
        if patient is not None and conv.patient_id is None:
            conv.patient = patient
            conv.save(update_fields=["patient"])
        if conv.laboratory_id is None:
            conv.laboratory = _first_lab()
            conv.save(update_fields=["laboratory"])

        # idempotência: mesma mensagem do provedor não é reprocessada (CT-INT-008)
        if WhatsAppMessage.objects.filter(provider_message_id=message_id).exists():
            return conv

        inbound = WhatsAppMessage.objects.create(
            conversation=conv,
            provider_message_id=message_id,
            direction=Direction.INBOUND,
            content=text
            or (
                f"📍 Localização compartilhada: {coords[0]}, {coords[1]}"
                if coords is not None
                else ""
            ),
        )
        if coords is not None:
            # D-01: localização recebida -> resolve a farmácia mais próxima de
            # forma determinística (sem custo/atraso de LLM).
            extraction = {
                "intent": "nearest_pharmacy",
                "confidence": 1.0,
                "location": {"latitude": coords[0], "longitude": coords[1]},
            }
            model = ""
            used_mock = False
            ai_error = False
        elif WhatsAppService._looks_like_nearest_pharmacy_ask(text):
            extraction = {"intent": "nearest_pharmacy", "confidence": 1.0, "location": None}
            model = ""
            used_mock = False
            ai_error = False
        elif PROTOCOL_RE.search(text):
            # protocolo presente: consulta de andamento é determinística (sem IA)
            extraction = {
                "intent": "check_status",
                "confidence": 1.0,
                "protocol": PROTOCOL_RE.search(text).group(0).upper(),
            }
            model = ""
            used_mock = False
            ai_error = False
        else:
            try:
                extraction, model, used_mock, ai_error = WhatsAppService.analyze(text)
            except ExtractionError as exc:
                extraction = {"intent": "help", "confidence": 0.0}
                model = ""
                used_mock = True
                ai_error = True
                logger.warning("Extração inválida da IA: %s", exc)
        # reforço: se a intenção for check_status, garante o protocolo na extração
        if extraction.get("intent") == "check_status" and not extraction.get("protocol"):
            m = PROTOCOL_RE.search(text)
            if m:
                extraction["protocol"] = m.group(0).upper()
        inbound.ai_interpretation = extraction
        inbound.ai_model = model
        inbound.ai_used_mock = used_mock
        inbound.ai_error = ai_error
        inbound.save(
            update_fields=["ai_interpretation", "ai_model", "ai_used_mock", "ai_error"]
        )
        reply = WhatsAppService._act(extraction, conv)
        WhatsAppMessage.objects.create(
            conversation=conv,
            direction=Direction.OUTBOUND,
            content=reply,
        )
        audit_record(
            action="whatsapp.message_processed",
            entity_type="whatsapp.Conversation",
            entity_id=conv.pk,
            laboratory=conv.laboratory,
            metadata={"intent": extraction.get("intent"), "mock": used_mock},
        )
        return conv

    @staticmethod
    def clear_memory(conv, *, by_user=None):
        """Zera e reinicia a conversa (homologação): apaga mensagens e reabre."""
        from apps.audit.models import record as audit_record

        cleared = conv.messages.count()
        conv.messages.all().delete()
        conv.status = "open"
        conv.save(update_fields=["status", "updated_at"])
        audit_record(
            action="whatsapp.memory_cleared",
            entity_type="whatsapp.Conversation",
            entity_id=conv.pk,
            laboratory=conv.laboratory,
            user=by_user if (by_user and by_user.is_authenticated) else None,
            metadata={"cleared": cleared},
        )
        return cleared

    @staticmethod
    def _act(extraction, conv):
        intent = extraction.get("intent")
        threshold = settings.AI_MIN_CONFIDENCE
        if float(extraction.get("confidence", 0)) < threshold or extraction.get("requires_human"):
            conv.status = "human"
            conv.save(update_fields=["status"])
            return (
                "Recebi sua mensagem. Para garantir a segurança das informações, "
                "um atendente humano vai te responder em instantes. "
                "Me diga também: qual exame deseja e em qual período prefere."
            )
        if intent == "create_collection_request":
            return WhatsAppService._create_request(extraction, conv)
        if intent == "check_status":
            return WhatsAppService._check_status(extraction, conv)
        if intent == "nearest_pharmacy":
            return WhatsAppService._nearest_pharmacy(extraction, conv)
        return (
            "Olá! Eu sou o assistente do Coleta Agendada. Posso ajudar você a "
            'solicitar uma coleta de exames (ex.: "quero agendar hemograma '
            'amanhã de manhã") ou consultar o andamento (envie o protocolo '
            "CA-...)."
        )

    @staticmethod
    def _create_request(extraction, conv):
        collection = extraction.get("collection") or {}
        exams = extraction.get("exams") or []
        if conv.patient_id is None:
            conv.status = "human"
            conv.save(update_fields=["status"])
            return (
                "Ainda não identifiquei seu cadastro por este canal. "
                "Um atendente vai confirmar seus dados e criar a solicitação."
            )
        if not exams:
            conv.status = "human"
            conv.save(update_fields=["status"])
            return (
                "Para solicitar a coleta, me diga qual(is) exame(s) deseja "
                "(ex.: hemograma, glicemia). Já encaminhei para um atendente "
                "te acompanhar também."
            )
        from apps.requests.models import CollectionRequest
        from apps.requests.services import RequestStateService
        from apps.requests.statuses import CollectionMode, DesiredPeriod

        desired_date = collection.get("desired_date") or None
        period = collection.get("desired_period") or ""
        mode = collection.get("mode") or CollectionMode.PHARMACY
        if mode not in CollectionMode.values:
            mode = CollectionMode.PHARMACY
        req = CollectionRequest.objects.create(
            patient=conv.patient,
            laboratory=conv.laboratory,
            desired_date=desired_date,
            desired_period=period if period in DesiredPeriod.values else "",
            collection_mode=mode,
            preferred_location=collection.get("preferred_location", ""),
        )
        RequestStateService.mark_created(req, changed_by=conv.patient.user, origin="whatsapp")
        items = [
            {
                "exam_code": ex.get("code") or "",
                "description": ex.get("name") or "",
                "quantity": ex.get("quantity") or 1,
            }
            for ex in exams
        ]
        draft_note = ""
        try:
            from apps.quotations.services import QuotationService

            QuotationService.create_draft(
                req,
                items,
                lab=conv.laboratory,
                created_by=None,
                generated_by_ai=True,
            )
            draft_note = (
                " Já preparei um rascunho de orçamento, que passará por "
                "validação humana antes de ser enviado a você."
            )
        except Exception:  # noqa: BLE001 — rascunho não deve impedir o registro
            logger.exception("Falha ao gerar rascunho IA da solicitação %s", req.protocol)
        audit_record(
            action="whatsapp.request_created",
            entity_type="requests.CollectionRequest",
            entity_id=req.pk,
            metadata={"protocol": req.protocol},
        )
        return (
            f"Solicitação registrada! Protocolo: {req.protocol}.{draft_note} "
            "Um atendente também acompanha o seu pedido."
        )

    @staticmethod
    def _check_status(extraction, conv):
        protocol = extraction.get("protocol")
        if not protocol or conv.patient_id is None:
            return "Envie o protocolo (formato CA-...) para eu consultar o andamento."
        from apps.requests.models import CollectionRequest

        req = CollectionRequest.objects.filter(
            protocol__iexact=protocol, patient=conv.patient
        ).first()
        if req is None:
            return "Não encontrei uma solicitação com esse protocolo para o seu cadastro."
        return (
            f"Solicitação {req.protocol}: {req.get_status_display()}. "
            "Posso ajudar com mais alguma coisa?"
        )
    @staticmethod
    def _nearest_pharmacy(extraction, conv):
        """D-01: devolve o local de coleta mais próximo da localização.

        Ponto de coleta do domínio = farmácia OU laboratório (decisão do
        usuário 04/09/2026): busca o laboratório do canal (se tiver
        coordenadas) e as farmácias ativas com coordenadas da rede
        (conv.laboratory). Sem localização válida, pede o compartilhamento;
        sem ponto georreferenciado, encaminha a humano (não inventa ponto de
        coleta — regras 1/10 do AGENTS.md).
        """
        location = extraction.get("location") or {}
        lat, lon = location.get("latitude"), location.get("longitude")
        if lat is None or lon is None or not valid_coordinates(lat, lon):
            return (
                "Claro! Para te dizer o local de coleta mais próximo da rede, "
                "compartilhe sua localização atual pelo chat "
                "(ícone 📎 → Localização)."
            )
        lab = conv.laboratory
        if lab is None:
            conv.status = "human"
            conv.save(update_fields=["status"])
            return (
                "Ainda não identifiquei o laboratório deste canal. "
                "Um atendente humano vai te ajudar a escolher o ponto de coleta."
            )
        ranked = nearest_collection_points(lab.pk, float(lat), float(lon), limit=1)
        if not ranked:
            conv.status = "human"
            conv.save(update_fields=["status"])
            return (
                f"Ainda não há pontos de coleta da rede {lab.name} com "
                "localização cadastrada neste momento. Um atendente humano vai "
                "te indicar o local de coleta mais próximo em instantes."
            )
        distance_km, kind, point = ranked[0]
        if kind == "laboratory":
            subject = f"o laboratório {point.name}"
        else:
            subject = f"a farmácia {point.name}"
        parts = [part for part in (point.address, point.city, point.state) if part]
        where = (" — " + ", ".join(parts)) if parts else ""
        schedule = point_services.schedule_summary(point)
        state = point_services.open_state_label(point)
        return (
            f"O local de coleta mais próximo da sua localização é {subject}"
            f"{where} (a cerca de {WhatsAppService._fmt_km(distance_km)} km). "
            f"Horário: {schedule}. No momento: {state}. Posso agendar a coleta "
            "nesse ponto para você? É só me dizer qual exame e em qual período "
            "prefere."
        )