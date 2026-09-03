"""Endpoints de pagamento (doc 07 §7) e webhook idempotente (CT-INT-008)."""
from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts import rbac
from apps.payments.models import Payment
from apps.payments.serializers import AmountSerializer, PaymentReadSerializer
from apps.payments.services import PaymentService
from apps.requests.models import CollectionRequest
from apps.requests.views import _can_view


def _lab_only(user):
    return user.role_code == rbac.LABORATORY


def _lab_or_pharmacy(user):
    return user.role_code in (rbac.LABORATORY, rbac.PHARMACY)


class RequestPaymentsView(APIView):
    """GET lista pagamentos (escopo); POST registra pagamento presencial (RF-015)."""

    def _request_or_deny(self, user, pk):
        req = CollectionRequest.objects.filter(pk=pk).first()
        if req is None or not _can_view(user, req):
            raise PermissionDenied()
        return req

    def get(self, request, pk=None):
        req = self._request_or_deny(request.user, pk)
        qs = Payment.objects.filter(request=req).order_by("-created_at")
        return Response(PaymentReadSerializer(qs, many=True).data)

    def post(self, request, pk=None):
        if not _lab_or_pharmacy(request.user):
            raise PermissionDenied("Permitido para laboratório/farmácia.")
        req = self._request_or_deny(request.user, pk)
        ser = AmountSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        payment = PaymentService.register_presential(
            req, amount=ser.validated_data["amount"], created_by=request.user,
            http_request=request,
        )
        return Response(
            PaymentReadSerializer(payment).data, status=status.HTTP_201_CREATED
        )


class PaymentLinkView(APIView):
    """POST /requests/{pk}/payments/link — link opcional (RF-014; adapter fake)."""

    def post(self, request, pk=None):
        req = CollectionRequest.objects.filter(pk=pk).first()
        if req is None:
            raise PermissionDenied()
        if not _lab_only(request.user):
            raise PermissionDenied("Somente o laboratório pode gerar link de pagamento.")
        ser = AmountSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        payment = PaymentService.create_link(
            req, amount=ser.validated_data["amount"], created_by=request.user,
            http_request=request,
        )
        return Response(
            PaymentReadSerializer(payment).data, status=status.HTTP_201_CREATED
        )


class PaymentDetailView(APIView):
    def get(self, request, pk=None):
        payment = Payment.objects.select_related("request__patient__user").filter(pk=pk).first()
        if payment is None or not _can_view(request.user, payment.request):
            raise PermissionDenied()
        return Response(PaymentReadSerializer(payment).data)


class PaymentConfirmView(APIView):
    """POST /payments/{pk}/confirm — confirmação financeira (manual)."""

    def post(self, request, pk=None):
        payment = Payment.objects.filter(pk=pk).first()
        if payment is None:
            raise PermissionDenied()
        if not _lab_only(request.user):
            raise PermissionDenied("Somente o laboratório confirma pagamentos.")
        PaymentService.confirm(payment, confirmed_by=request.user, http_request=request)
        return Response(PaymentReadSerializer(payment).data)


class PaymentWebhookView(APIView):
    """POST /payments/webhook — callback do provedor (CT-INT-008 idempotente).

    Segurança: se PAYMENT_WEBHOOK_SECRET estiver definido, exige o header
    X-Webhook-Secret correspondente (MVP roda sem secret em dev — nota G-02).
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        secret = getattr(settings, "PAYMENT_WEBHOOK_SECRET", "")
        if secret and request.headers.get("X-Webhook-Secret", "") != secret:
            raise PermissionDenied("Webhook não autorizado.")
        external = (request.data.get("external_reference") or "").strip()
        event = (request.data.get("status") or "").lower()
        if not external or not event:
            return Response(
                {
                    "error": {
                        "code": "invalid",
                        "message": "external_reference e status são obrigatórios.",
                        "details": {},
                    }
                },
                status=400,
            )
        payment = PaymentService.handle_webhook(external, event, http_request=request)
        return Response(PaymentReadSerializer(payment).data)
