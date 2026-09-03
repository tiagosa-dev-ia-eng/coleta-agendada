from rest_framework import status
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts import rbac
from apps.organizations import scope
from apps.quotations.models import Quotation
from apps.quotations.serializers import DraftCreateSerializer, QuotationReadSerializer
from apps.quotations.services import QuotationService
from apps.requests.models import CollectionRequest
from apps.requests.views import _can_view


def _can_attend(user):
    """Laboratório (validação/envio) — permissões quotation.review/send."""
    return rbac.has_permission(user, "quotation.review") and rbac.has_permission(
        user, "quotation.send"
    )


class QuotationDraftView(APIView):
    """POST /requests/{pk}/quotation-draft — rascunho com preços do catálogo (G-01)."""

    def post(self, request, pk=None):
        req = CollectionRequest.objects.filter(pk=pk).first()
        if req is None:
            raise PermissionDenied()
        lab = scope.laboratory_of(request.user)
        if lab is None or not _can_attend(request.user):
            raise PermissionDenied()
        ser = DraftCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            quote = QuotationService.create_draft(
                req,
                ser.validated_data["items"],
                lab=lab,
                created_by=request.user,
                generated_by_ai=False,
            )
        except APIException as exc:
            raise exc
        return Response(QuotationReadSerializer(quote).data, status=status.HTTP_201_CREATED)


class RequestQuotationsView(APIView):
    """GET /requests/{pk}/quotations — versões visíveis ao escopo."""

    def get(self, request, pk=None):
        req = CollectionRequest.objects.filter(pk=pk).first()
        if req is None or not _can_view(request.user, req):
            raise PermissionDenied()
        quotes = Quotation.objects.filter(request=req).order_by("-version")
        return Response(QuotationReadSerializer(quotes, many=True).data)


class QuotationDetailView(APIView):
    def get(self, request, pk=None):
        quote = Quotation.objects.select_related("request__patient__user").filter(pk=pk).first()
        if quote is None or not _can_view(request.user, quote.request):
            raise PermissionDenied()
        return Response(QuotationReadSerializer(quote).data)


class QuotationValidateView(APIView):
    """POST /quotations/{pk}/validate — validação humana (RN-ORC-002)."""

    def post(self, request, pk=None):
        quote = Quotation.objects.select_related("request").filter(pk=pk).first()
        if quote is None or not _can_attend(request.user):
            raise PermissionDenied()
        final = QuotationService.validate_draft(quote, validated_by=request.user)
        return Response(QuotationReadSerializer(final).data)


class QuotationSendView(APIView):
    """POST /quotations/{pk}/send — só final validado (RN-ORC-003)."""

    def post(self, request, pk=None):
        quote = Quotation.objects.select_related("request").filter(pk=pk).first()
        if quote is None or not _can_attend(request.user):
            raise PermissionDenied()
        sent = QuotationService.send(quote, sent_by=request.user)
        return Response(QuotationReadSerializer(sent).data)


class QuotationApproveView(APIView):
    """POST /quotations/{pk}/approve — aprovação do paciente (RF-008)."""

    def post(self, request, pk=None):
        quote = Quotation.objects.select_related("request__patient__user").filter(pk=pk).first()
        if quote is None:
            raise PermissionDenied()
        if quote.request.patient.user_id != request.user.pk:
            raise PermissionDenied("Somente o paciente titular pode aprovar o orçamento.")
        approved = QuotationService.approve(quote, approved_by=request.user)
        return Response(QuotationReadSerializer(approved).data)


class QuotationRejectView(APIView):
    """POST /quotations/{pk}/reject — recusa do paciente -> solicitação cancelada."""

    def post(self, request, pk=None):
        quote = Quotation.objects.select_related("request__patient__user").filter(pk=pk).first()
        if quote is None:
            raise PermissionDenied()
        if quote.request.patient.user_id != request.user.pk:
            raise PermissionDenied("Somente o paciente titular pode recusar o orçamento.")
        rejected = QuotationService.reject(
            quote, rejected_by=request.user, reason=request.data.get("reason", "")
        )
        return Response(QuotationReadSerializer(rejected).data)
