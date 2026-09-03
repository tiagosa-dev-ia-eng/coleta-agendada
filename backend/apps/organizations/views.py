from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from apps.accounts import rbac
from apps.audit.models import record as audit_record
from apps.organizations import scope
from apps.organizations.models import Laboratory, Pharmacy, Reseller
from apps.organizations.serializers import (
    LaboratorySerializer,
    PharmacyCreateSerializer,
    ResellerCreateSerializer,
)


class PermissionByCodes(BasePermission):
    """Permissão por lista de códigos do catálogo (doc 04/16)."""

    def __init__(self, *codes):
        super().__init__()
        self.codes = codes

    def has_permission(self, request, view):
        return any(rbac.has_permission(request.user, code) for code in self.codes)


def audit(request, action, entity_type, entity_id, metadata=None):
    audit_record(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user=request.user,
        ip=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        metadata=metadata or {},
    )


def own_lab_queryset(request, model):
    lab = scope.laboratory_of(request.user)
    if rbac.has_permission(request.user, "dashboard.view"):
        return model.objects.all()
    if lab is None:
        return model.objects.none()
    return model.objects.filter(pk=lab.pk)


class LaboratoryViewSet(viewsets.GenericViewSet):
    """Laboratórios: laboratório administra; demais perfis leem a própria organização."""

    serializer_class = LaboratorySerializer
    queryset = Laboratory.objects.all()

    def get_permissions(self):
        if self.action in ("create", "partial_update", "update"):
            return [IsAuthenticated(), PermissionByCodes("user.manage")]
        return [IsAuthenticated()]

    def list(self, request):
        qs = own_lab_queryset(request, Laboratory)
        return Response(self.serializer_class(qs, many=True).data)

    def retrieve(self, request, pk=None):
        qs = own_lab_queryset(request, Laboratory)
        lab = qs.filter(pk=pk).first()
        if lab is None:
            raise PermissionDenied()
        return Response(self.serializer_class(lab).data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        lab = serializer.save()
        if request.user.role_code == rbac.LABORATORY and not hasattr(
            request.user, "owned_laboratory"
        ):
            lab.owner = request.user
            lab.save(update_fields=["owner"])
        audit(request, "laboratory.created", "laboratory", lab.pk, {"name": lab.name})
        return Response(self.serializer_class(lab).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        lab = Laboratory.objects.filter(pk=pk).first()
        if lab is None or not rbac.has_permission(request.user, "dashboard.view"):
            raise PermissionDenied()
        serializer = self.serializer_class(lab, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(self.serializer_class(lab).data)


class ResellerViewSet(viewsets.GenericViewSet):
    """Revendedores: somente o laboratório cadastra, na própria organização."""

    serializer_class = ResellerCreateSerializer

    def get_queryset(self):
        lab = scope.laboratory_of(self.request.user)
        return Reseller.objects.filter(laboratory=lab) if lab else Reseller.objects.none()

    def get_permissions(self):
        return [IsAuthenticated(), PermissionByCodes("user.manage")]

    def list(self, request):
        return Response(self.serializer_class(self.get_queryset(), many=True).data)

    def create(self, request):
        if not scope.is_laboratory_admin(request.user):
            raise PermissionDenied("Somente o laboratório pode cadastrar revendedores.")
        ctx = {
            "request": request,
            "laboratory": request.user.owned_laboratory,
        }
        serializer = self.serializer_class(data=request.data, context=ctx)
        serializer.is_valid(raise_exception=True)
        reseller = serializer.save()
        return Response(self.serializer_class(reseller).data, status=status.HTTP_201_CREATED)


class PharmacyViewSet(viewsets.GenericViewSet):
    """Farmácias: laboratório/revendedor criam e gerenciam; escopo por rede."""

    serializer_class = PharmacyCreateSerializer

    def get_queryset(self):
        lab = scope.laboratory_of(self.request.user)
        if lab is None:
            return Pharmacy.objects.none()
        qs = Pharmacy.objects.filter(laboratory=lab)
        if self.request.user.role_code == rbac.RESELLER:
            qs = qs.filter(reseller=self.request.user.reseller_profile)
        if self.request.user.role_code == rbac.PHARMACY:
            qs = qs.filter(user=self.request.user)
        return qs.order_by("name")

    def get_permissions(self):
        if self.action in ("list", "create", "partial_update", "update"):
            return [IsAuthenticated(), PermissionByCodes("pharmacy.manage")]
        return [IsAuthenticated()]

    def list(self, request):
        return Response(self.serializer_class(self.get_queryset(), many=True).data)

    def retrieve(self, request, pk=None):
        pharmacy = Pharmacy.objects.filter(pk=pk).first()
        own = (
            request.user.role_code == rbac.PHARMACY
            and getattr(request.user, "pharmacy_profile", None) is not None
            and pharmacy is not None
            and request.user.pharmacy_profile.pk == pharmacy.pk
        )
        if pharmacy is None or (pharmacy not in self.get_queryset() and not own):
            raise PermissionDenied()
        return Response(self.serializer_class(pharmacy).data)

    def create(self, request):
        lab = scope.laboratory_of(request.user)
        if lab is None:
            raise PermissionDenied()
        ctx = {"request": request, "laboratory": lab}
        if request.user.role_code == rbac.RESELLER:
            ctx["reseller"] = request.user.reseller_profile
        serializer = self.serializer_class(data=request.data, context=ctx)
        serializer.is_valid(raise_exception=True)
        pharmacy = serializer.save()
        return Response(self.serializer_class(pharmacy).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        pharmacy = self.get_queryset().filter(pk=pk).first()
        if pharmacy is None:
            raise PermissionDenied()
        serializer = self.serializer_class(
            pharmacy, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(self.serializer_class(pharmacy).data)
