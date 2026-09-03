"""QuotationService — regras de orçamento (RN-ORC-001..005, doc 09)."""
from decimal import Decimal

from django.utils import timezone
from rest_framework.exceptions import APIException

from apps.audit.models import record as audit_record
from apps.catalog.models import Exam, ExamPrice
from apps.quotations.models import ItemSource, Quotation, QuotationItem, QuotationType
from apps.requests.services import RequestStateService
from apps.requests.statuses import RequestStatus


class QuotationError(APIException):
    status_code = 409
    default_code = "quotation_error"
    default_detail = "Operação inválida para este orçamento."


class QuoteNotValidated(QuotationError):
    """RN-ORC-003: envio exige validação humana (doc 07 §5)."""

    default_code = "quote_not_validated"
    default_detail = "O orçamento final precisa de validação humana antes do envio."


class MissingPrices(QuotationError):
    status_code = 422
    default_code = "quote_items_missing_price"
    default_detail = "Há itens sem preço definido; defina o preço do exame ou ajuste o item."


def _price_for(lab, exam):
    row = ExamPrice.objects.filter(laboratory=lab, exam=exam, active=True).first()
    return row.price if row else None


class QuotationService:
    """Serviço de domínio de orçamentos (rascunho → validação humana → envio)."""

    @staticmethod
    def _next_version(request_obj):
        latest = Quotation.objects.filter(request=request_obj).order_by("-version").first()
        return (latest.version + 1) if latest else 1

    @staticmethod
    def _total(items):
        total = Decimal("0.00")
        for it in items:
            if it.unit_price is not None:
                total += Decimal(it.quantity) * it.unit_price
        return total

    @staticmethod
    def create_draft(request_obj, items, *, lab, created_by=None, generated_by_ai=False):
        """Cria rascunho (vN) precificando pelos itens do catálogo do laboratório.

        Items: lista de dicts {exam_code?: str, description?: str, quantity?: int}.
        Exame desconhecido/ausente -> item sem preço (exige humano) com source manual.
        """
        if request_obj.laboratory_id is None:
            request_obj.laboratory = lab
            request_obj.save(update_fields=["laboratory", "updated_at"])
        if request_obj.status == RequestStatus.REQUESTED:
            RequestStateService.transition(
                request_obj, RequestStatus.QUOTE_DRAFT, changed_by=created_by, origin="system"
            )
        elif request_obj.status != RequestStatus.QUOTE_DRAFT:
            raise QuotationError(detail="Solicitação não está em estado de rascunho de orçamento.")

        quote = Quotation.objects.create(
            request=request_obj,
            version=QuotationService._next_version(request_obj),
            quotation_type=QuotationType.DRAFT,
            generated_by_ai=generated_by_ai,
            created_by=created_by,
        )
        for raw in items:
            exam = None
            description = (raw.get("description") or "").strip()
            code = (raw.get("exam_code") or "").strip()
            if code:
                exam = Exam.objects.filter(code__iexact=code, active=True).first()
            if exam is None and not description:
                raise QuotationError(detail="Item sem exame (exam_code) nem descrição.")
            unit_price = None
            source = ItemSource.MANUAL
            if exam is not None:
                unit_price = _price_for(lab, exam)
                source = ItemSource.CATALOG
                description = description or exam.name
            elif generated_by_ai:
                source = ItemSource.AI
            try:
                quantity = int(raw.get("quantity") or 1)
            except (TypeError, ValueError):
                quantity = 1
            if quantity < 1:
                quantity = 1
            QuotationItem.objects.create(
                quotation=quote,
                exam=exam,
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                source=source,
            )
        items_qs = list(quote.items.all())
        quote.subtotal = QuotationService._total(items_qs)
        quote.total = quote.subtotal
        quote.save(update_fields=["subtotal", "total"])
        audit_record(
            action="quotation.draft_created",
            entity_type="quotations.Quotation",
            entity_id=quote.pk,
            user=created_by,
            metadata={"protocol": request_obj.protocol, "version": quote.version},
        )
        return quote

    @staticmethod
    def validate_draft(quote, *, validated_by):
        """RN-ORC-001/002: promove o rascunho em orçamento FINAL validado (vN+1)."""
        if quote.is_final:
            raise QuotationError(
                detail="Este orçamento já é final (crie um novo rascunho para revisar)."
            )
        if quote.missing_price_count:
            raise MissingPrices()
        request_obj = quote.request
        # cria a versão final copiando itens
        final = Quotation.objects.create(
            request=request_obj,
            version=QuotationService._next_version(request_obj),
            quotation_type=QuotationType.FINAL,
            generated_by_ai=quote.generated_by_ai,
            notes=quote.notes,
            subtotal=quote.subtotal,
            total=quote.total,
            created_by=quote.created_by,
            validated_by=validated_by,
            validated_at=timezone.now(),
        )
        for item in quote.items.all():
            QuotationItem.objects.create(
                quotation=final,
                exam=item.exam,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                source=item.source,
            )
        if request_obj.status == RequestStatus.QUOTE_DRAFT:
            RequestStateService.transition(
                request_obj,
                RequestStatus.WAITING_HUMAN_VALIDATION,
                changed_by=validated_by,
                origin="user",
                reason="Orçamento final validado (RN-ORC-002)",
            )
        audit_record(
            action="quotation.validated",
            entity_type="quotations.Quotation",
            entity_id=final.pk,
            user=validated_by,
            metadata={"protocol": request_obj.protocol, "version": final.version},
        )
        return final

    @staticmethod
    def send(final_quote, *, sent_by):
        """RN-ORC-003/07: somente orçamento final validado pode ser enviado."""
        if not final_quote.is_final or not final_quote.is_validated:
            # RN-ORC-003: envio exige final validado (rascunho também cai aqui)
            raise QuoteNotValidated()
        if final_quote.is_sent:
            raise QuotationError(detail="Orçamento já foi enviado.")
        final_quote.sent_at = timezone.now()
        final_quote.save(update_fields=["sent_at", "updated_at"])
        request_obj = final_quote.request
        if request_obj.status == RequestStatus.WAITING_HUMAN_VALIDATION:
            RequestStateService.transition(
                request_obj,
                RequestStatus.QUOTE_SENT,
                changed_by=sent_by,
                origin="user",
                reason="Orçamento final enviado ao paciente",
            )
        audit_record(
            action="quotation.sent",
            entity_type="quotations.Quotation",
            entity_id=final_quote.pk,
            user=sent_by,
            metadata={"protocol": request_obj.protocol, "version": final_quote.version},
        )
        return final_quote

    @staticmethod
    def approve(final_quote, *, approved_by):
        """Aprovação pelo paciente (RF-008)."""
        if not final_quote.is_final or not final_quote.is_validated or not final_quote.is_sent:
            raise QuotationError(detail="Orçamento ainda não foi enviado para aprovação.")
        if final_quote.is_approved:
            raise QuotationError(detail="Orçamento já aprovado.")
        final_quote.approved_by = approved_by
        final_quote.approved_at = timezone.now()
        final_quote.save(update_fields=["approved_by", "approved_at", "updated_at"])
        request_obj = final_quote.request
        if request_obj.status == RequestStatus.QUOTE_SENT:
            RequestStateService.transition(
                request_obj,
                RequestStatus.APPROVED,
                changed_by=approved_by,
                origin="user",
                reason="Orçamento aprovado pelo paciente",
            )
        audit_record(
            action="quotation.approved",
            entity_type="quotations.Quotation",
            entity_id=final_quote.pk,
            user=approved_by,
            metadata={"protocol": request_obj.protocol, "version": final_quote.version},
        )
        return final_quote

    @staticmethod
    def reject(final_quote, *, rejected_by, reason=""):
        """Recusa do paciente -> solicitação cancelada (doc 05: enviado -> cancelado)."""
        final_quote.rejected_by = rejected_by
        final_quote.rejected_at = timezone.now()
        final_quote.save(update_fields=["rejected_by", "rejected_at", "updated_at"])
        RequestStateService.cancel(
            final_quote.request,
            changed_by=rejected_by,
            origin="user",
            reason=reason or "Orçamento recusado",
        )
        audit_record(
            action="quotation.rejected",
            entity_type="quotations.Quotation",
            entity_id=final_quote.pk,
            user=rejected_by,
            metadata={"protocol": final_quote.request.protocol},
        )
        return final_quote
