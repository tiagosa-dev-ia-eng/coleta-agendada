"""PaymentService — transições de pagamento (doc 10) e webhook idempotente."""
from django.utils import timezone
from rest_framework.exceptions import APIException

from apps.audit.models import record as audit_record
from apps.payments.gateway import get_gateway
from apps.payments.models import Payment, PaymentMethod, PaymentStatus

ALLOWED = {
    PaymentStatus.PENDING: {
        PaymentStatus.LINK_CREATED,
        PaymentStatus.CONFIRMED,
        PaymentStatus.FAILED,
        PaymentStatus.CANCELED,
    },
    PaymentStatus.LINK_CREATED: {
        PaymentStatus.AUTHORIZED,
        PaymentStatus.CONFIRMED,
        PaymentStatus.FAILED,
        PaymentStatus.CANCELED,
    },
    PaymentStatus.AUTHORIZED: {PaymentStatus.CONFIRMED, PaymentStatus.FAILED},
    PaymentStatus.CONFIRMED: {PaymentStatus.REFUNDED},
    PaymentStatus.FAILED: set(),
    PaymentStatus.REFUNDED: set(),
    PaymentStatus.CANCELED: set(),
}

ALLOWED_BILLING_STATES = {
    "APPROVED",
    "SCHEDULED",
    "IN_PROGRESS",
    "COMPLETED",
}


class PaymentError(APIException):
    status_code = 409
    default_code = "payment_error"
    default_detail = "Operação inválida para este pagamento."


class PaymentNotFound(APIException):
    status_code = 404
    default_code = "payment_not_found"
    default_detail = "Pagamento não encontrado."


def _transition(payment, to_status):
    allowed = {str(s) for s in ALLOWED.get(payment.status, set())}
    if str(to_status) not in allowed:
        raise PaymentError(
            detail=f"Transição {payment.status} -> {to_status} não permitida."
        )
    payment.status = to_status
    payment.save(update_fields=["status", "updated_at"])
    return payment


def _audit(request, action, payment, metadata=None):
    audit_record(
        action=action,
        entity_type="payments.Payment",
        entity_id=payment.pk,
        user=(
            request.user
            if request is not None and request.user.is_authenticated
            else None
        ),
        ip=request.META.get("REMOTE_ADDR") if request is not None else None,
        user_agent=request.META.get("HTTP_USER_AGENT", "") if request is not None else "",
        metadata=metadata or {},
    )


class PaymentService:
    @staticmethod
    def create_link(request_obj, *, amount, created_by, http_request=None):
        """RF-014: link de pagamento opcional (via adapter — G-02 roda fake)."""
        if request_obj.status not in ALLOWED_BILLING_STATES:
            raise PaymentError(detail="Solicitação não permite cobrança neste estado.")
        payment = Payment.objects.create(
            request=request_obj,
            amount=amount,
            method=PaymentMethod.LINK,
            status=PaymentStatus.LINK_CREATED,
            created_by=created_by,
            gateway_provider=get_gateway().provider,
        )
        result = get_gateway().create_link(payment)
        payment.payment_url = result["url"]
        payment.external_reference = result.get("external_reference") or payment.code
        payment.save(update_fields=["payment_url", "external_reference", "updated_at"])
        _audit(http_request, "payment.link_created", payment, {"code": payment.code})
        return payment

    @staticmethod
    def register_presential(request_obj, *, amount, created_by, http_request=None):
        """RF-015: pagamento presencial na coleta (registrado pelo operador)."""
        payment = Payment.objects.create(
            request=request_obj,
            amount=amount,
            method=PaymentMethod.PRESENTIAL,
            status=PaymentStatus.PENDING,
            created_by=created_by,
        )
        _audit(http_request, "payment.presential_registered", payment, {"code": payment.code})
        return payment

    @staticmethod
    def confirm(payment, *, confirmed_by=None, http_request=None, origin="manual"):
        """Confirma manual (financeiro) ou via webhook. Idempotente quando CONFIRMED."""
        if payment.status == PaymentStatus.CONFIRMED and payment.paid_at:
            return payment  # idempotente
        _transition(payment, PaymentStatus.CONFIRMED)
        payment.paid_at = timezone.now()
        payment.save(update_fields=["paid_at", "updated_at"])
        _audit(
            http_request,
            "payment.confirmed",
            payment,
            {"origin": origin, "code": payment.code},
        )
        # G-03: comissões PERCENTUAIS geram na confirmação (base = valor pago)
        from apps.commissions.services import trigger_percentage_on_payment

        trigger_percentage_on_payment(payment.request, payment)
        return payment

    @staticmethod
    def handle_webhook(external_reference, event_status, *, http_request=None):
        """Webhook do provedor (CT-INT-008 — idempotente por external_reference)."""
        payment = Payment.objects.select_for_update().filter(
            external_reference=external_reference
        ).first()
        if payment is None:
            raise PaymentNotFound()
        if event_status in ("confirmed", "paid", "approved"):
            return PaymentService.confirm(
                payment,
                confirmed_by=payment.created_by,
                http_request=http_request,
                origin="webhook",
            )
        if event_status in ("failed", "refused", "cancelled", "canceled"):
            return _transition(payment, PaymentStatus.FAILED)
        return payment
