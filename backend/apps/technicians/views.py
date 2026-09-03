from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from apps.accounts import rbac
from apps.organizations import scope
from apps.technicians.models import Technician
from apps.technicians.serializers import TechnicianCreateSerializer


class _ManagePermission(BasePermission):
    message = "Você não possui permissão para esta ação."

    def has_permission(self, request, view):
        return rbac.has_permission(request.user, "technician.manage")


class TechnicianViewSet(viewsets.GenericViewSet):
    """Técnicos da rede: laboratório/revendedor gerem; técnico vê o próprio perfil."""

    serializer_class = TechnicianCreateSerializer

    def get_queryset(self):
        lab = scope.laboratory_of(self.request.user)
        if lab is None:
            return Technician.objects.none()
        qs = Technician.objects.filter(laboratory=lab)
        if self.request.user.role_code == rbac.RESELLER:
            qs = qs.filter(reseller=self.request.user.reseller_profile)
        return qs.order_by("-created_at")

    def get_permissions(self):
        if self.action in ("list", "create", "partial_update"):
            return [IsAuthenticated(), _ManagePermission()]
        return [IsAuthenticated()]

    def list(self, request):
        return Response(self.serializer_class(self.get_queryset(), many=True).data)

    def retrieve(self, request, pk=None):
        tech = Technician.objects.filter(pk=pk).first()
        if tech is None or tech not in self.get_queryset():
            own = (
                request.user.role_code == rbac.TECHNICIAN
                and getattr(request.user, "technician_profile", None) is not None
                and request.user.technician_profile.pk == int(pk)
            )
            if not own:
                raise PermissionDenied()
        return Response(self.serializer_class(tech).data)

    def create(self, request):
        lab = scope.laboratory_of(request.user)
        if lab is None:
            raise PermissionDenied()
        ctx = {"request": request, "laboratory": lab}
        if request.user.role_code == rbac.RESELLER:
            ctx["reseller"] = request.user.reseller_profile
        serializer = self.serializer_class(data=request.data, context=ctx)
        serializer.is_valid(raise_exception=True)
        tech = serializer.save()
        return Response(self.serializer_class(tech).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        tech = self.get_queryset().filter(pk=pk).first()
        if tech is None:
            raise PermissionDenied()
        serializer = self.serializer_class(
            tech, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        tech = serializer.save()
        return Response(self.serializer_class(tech).data)
