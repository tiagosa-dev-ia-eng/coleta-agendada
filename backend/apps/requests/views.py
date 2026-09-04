"""Endpoints de solicitações, pedido médico e histórico (docs 05, 07 §3-4)."""
from pathlib import Path

from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.accounts import rbac
from apps.audit.models import record as audit_record
from apps.requests.models import CollectionRequest, MedicalOrder
from apps.requests.serializers import (
    CollectionRequestCreateSerializer,
    CollectionRequestSerializer,
    MedicalOrderSerializer,
)
from apps.requests.services import InvalidTransition, RequestStateService

ALLOWED_MEDICAL_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}


class InvalidFile(APIException):
    status_code = 400
    default_code = "invalid_file"
    default_detail = "Arquivo inválido para o pedido médico."


def _lab(user):
    return rbac.has_permission(user, "dashboard.view")


def _can_view(user, req):
    """Escopo de leitura (doc 04 §4): paciente vê as próprias; laboratório vê a operação."""
    if user.is_superuser or _lab(user):
        return True
    if user.role_code == rbac.PATIENT:
        return req.patient.user_id == user.pk
    return False


class RequestViewSet(GenericViewSet):
    """CRUD/operações de solicitação com escopo por perfil."""

    serializer_class = CollectionRequestSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        qs = CollectionRequest.objects.select_related("patient__user").order_by("-created_at")
        if user.is_superuser or _lab(user):
            return qs
        if user.role_code == rbac.PATIENT:
            return qs.filter(patient__user=user)
        # reseller: rede ainda não vinculada (M4+); demais perfis sem vínculo: vazio
        return CollectionRequest.objects.none()

    # ---------- list / retrieve ----------
    def list(self, request):
        qs = self.get_queryset()
        payload = CollectionRequestSerializer(qs, many=True).data
        return Response(payload)

    def retrieve(self, request, pk=None):
        req = CollectionRequest.objects.filter(pk=pk).select_related("patient__user").first()
        if req is None or not _can_view(request.user, req):
            raise PermissionDenied()
        data = CollectionRequestSerializer(
            req,
            context={"request": request},
        ).data
        data["status_history"] = [
            {
                "from_status": h.from_status,
                "to_status": h.to_status,
                "origin": h.origin,
                "reason": h.reason,
                "created_at": h.created_at.isoformat(),
            }
            for h in req.status_history.all()
        ]
        return Response(data)

    # ---------- create (paciente) ----------
    def create(self, request):
        if not rbac.has_permission(request.user, "request.create"):
            raise PermissionDenied("Somente pacientes podem criar solicitações.")
        serializer = CollectionRequestCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        req = serializer.save()
        data = CollectionRequestSerializer(
            req, context={"request": request}
        ).data
        data["status_history"] = [
            {
                "from_status": h.from_status,
                "to_status": h.to_status,
                "origin": h.origin,
                "reason": h.reason,
                "created_at": h.created_at.isoformat(),
            }
            for h in req.status_history.all()
        ]
        return Response(data, status=status.HTTP_201_CREATED)

    # ---------- cancel (doc 05) ----------
    def cancel(self, request, pk=None):
        req = CollectionRequest.objects.filter(pk=pk).first()
        if req is None or not _can_view(request.user, req):
            raise PermissionDenied()
        try:
            RequestStateService.cancel(
                req,
                changed_by=request.user,
                origin="user",
                reason=request.data.get("reason", ""),
            )
        except InvalidTransition as exc:
            raise exc
        return Response({"status": req.status, "protocol": req.protocol})

    # ---------- history ----------
    def history(self, request, pk=None):
        req = CollectionRequest.objects.filter(pk=pk).first()
        if req is None or not _can_view(request.user, req):
            raise PermissionDenied()
        rows = [
            {
                "from_status": h.from_status,
                "to_status": h.to_status,
                "origin": h.origin,
                "reason": h.reason,
                "created_at": h.created_at.isoformat(),
            }
            for h in req.status_history.order_by("created_at")
        ]
        return Response(rows)

    # ---------- medical orders (storage local — G-07) ----------
    def list_medical_orders(self, request, pk=None):
        req = CollectionRequest.objects.filter(pk=pk).first()
        if req is None or not _can_view(request.user, req):
            raise PermissionDenied()
        return Response(
            MedicalOrderSerializer(
                req.medical_orders.all(), many=True, context={"request": request}
            ).data
        )

    def upload_medical_order(self, request, pk=None):
        req = CollectionRequest.objects.filter(pk=pk).first()
        if req is None or not _can_view(request.user, req):
            raise PermissionDenied()
        file = request.FILES.get("file")
        if file is None:
            raise InvalidFile(detail="Envie o arquivo no campo 'file'.")
        suffix = Path(file.name).suffix.lower()
        content_type = (file.content_type or "").lower()
        valid_type = content_type == "application/pdf" or content_type.startswith("image/")
        if suffix not in ALLOWED_MEDICAL_EXTENSIONS or not valid_type:
            raise InvalidFile(
                detail=(
                    "Formato não suportado. Envie PDF ou imagem "
                    f"({', '.join(sorted(ALLOWED_MEDICAL_EXTENSIONS))})."
                )
            )
        if file.size > settings.MAX_MEDICAL_UPLOAD_BYTES:
            limit_mb = settings.MAX_MEDICAL_UPLOAD_BYTES // (1024 * 1024)
            raise InvalidFile(detail=f"Arquivo excede o limite de {limit_mb} MB.")
        order = MedicalOrder.objects.create(
            request=req,
            file=file,
            mime_type=content_type,
            original_name=file.name,
            size=file.size,
            uploaded_by=request.user,
        )
        audit_record(
            action="medical_order.uploaded",
            entity_type="requests.MedicalOrder",
            entity_id=order.pk,
            user=request.user,
            ip=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            metadata={
                "protocol": req.protocol,
                "original_name": order.original_name,
                "size": order.size,
            },
        )
        return Response(
            MedicalOrderSerializer(order, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def upload_medical_attachments(self, request, pk=None):
        """Recebe VÁRIAS imagens/documentos (receita) de uma vez (D-05)."""
        req = CollectionRequest.objects.filter(pk=pk).first()
        if req is None or not _can_view(request.user, req):
            raise PermissionDenied()
        files = request.FILES.getlist("files")
        if not files:
            raise InvalidFile(detail="Envie um ou mais arquivos no campo 'files'.")
        created = []
        for file in files:
            suffix = Path(file.name).suffix.lower()
            content_type = (file.content_type or "").lower()
            valid_type = content_type == "application/pdf" or content_type.startswith("image/")
            if suffix not in ALLOWED_MEDICAL_EXTENSIONS or not valid_type:
                raise InvalidFile(
                    detail=(
                        "Formato não suportado. Envie PDF ou imagem "
                        f"({', '.join(sorted(ALLOWED_MEDICAL_EXTENSIONS))})."
                    )
                )
            if file.size > settings.MAX_MEDICAL_UPLOAD_BYTES:
                limit_mb = settings.MAX_MEDICAL_UPLOAD_BYTES // (1024 * 1024)
                raise InvalidFile(detail=f"Arquivo excede o limite de {limit_mb} MB.")
            order = MedicalOrder.objects.create(
                request=req,
                file=file,
                mime_type=content_type,
                original_name=file.name,
                size=file.size,
                uploaded_by=request.user,
            )
            audit_record(
                action="medical_order.uploaded",
                entity_type="requests.MedicalOrder",
                entity_id=order.pk,
                user=request.user,
                ip=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                metadata={
                    "protocol": req.protocol,
                    "original_name": order.original_name,
                    "size": order.size,
                    "batch": "prescription",
                },
            )
            created.append(order)
        return Response(
            MedicalOrderSerializer(created, many=True, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
