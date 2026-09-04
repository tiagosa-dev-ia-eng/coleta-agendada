"""Endpoints do Local de Coleta (D-03) — gestão e operação (abrir/fechar).

RBAC/escopo (docs/demandas.md D-03):
- Leitura: laboratório (rede), revendedor (farmácias da própria rede),
  farmácia (o próprio ponto) e técnico (pontos em que está designado).
- Gestão (criar/editar/janelas): laboratório e revendedor (pontos de
  farmácia da rede).
- Designação de técnico: SOMENTE laboratório (decisão do usuário).
- Abrir/fechar (check-in/check-out): técnico designado e ativo no ponto.
"""
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.accounts import rbac
from apps.collection_points import services
from apps.collection_points.models import (
    CollectionPoint,
    OpeningWindow,
    PointKind,
    TechnicianAssignment,
)
from apps.collection_points.serializers import (
    CollectionPointSerializer,
    OpeningWindowSerializer,
)
from apps.organizations import scope


def _manage_role(user):
    """Papel com poder de gestão do ponto (lab ou revendedor)."""
    if rbac.has_permission(user, "user.manage") and user.role_code == rbac.LABORATORY:
        return "laboratory"
    if rbac.has_permission(user, "pharmacy.manage") and user.role_code == rbac.RESELLER:
        return "reseller"
    return None


def _visible_qs(user):
    qs = CollectionPoint.objects.select_related(
        "laboratory", "pharmacy", "pharmacy__user"
    ).all()
    role = user.role_code
    if user.is_superuser or role == rbac.LABORATORY:
        lab = scope.laboratory_of(user)
        return qs.filter(laboratory=lab) if lab else qs.none()
    if role == rbac.RESELLER:
        prof = getattr(user, "reseller_profile", None)
        return (
            qs.filter(kind=PointKind.PHARMACY, pharmacy__reseller=prof)
            if prof
            else qs.none()
        )
    if role == rbac.PHARMACY:
        prof = getattr(user, "pharmacy_profile", None)
        return qs.filter(kind=PointKind.PHARMACY, pharmacy=prof) if prof else qs.none()
    if role == rbac.TECHNICIAN:
        prof = getattr(user, "technician_profile", None)
        return (
            qs.filter(technician_assignments__technician=prof)
            if prof
            else qs.none()
        )
    return qs.none()


class CollectionPointViewSet(GenericViewSet):
    serializer_class = CollectionPointSerializer
    queryset = CollectionPoint.objects.none()

    def get_queryset(self):
        return _visible_qs(self.request.user)

    # ---------- CRUD ----------

    def list(self, request):
        return Response(self.serializer_class(self.get_queryset(), many=True).data)

    def retrieve(self, request, pk=None):
        point = self.get_queryset().filter(pk=pk).first()
        if point is None:
            raise PermissionDenied()
        return Response(self.serializer_class(point).data)

    def _manager_lab(self, request):
        role = _manage_role(request.user)
        if role is None:
            raise PermissionDenied(
                "Somente laboratório ou revendedor gerencia pontos de coleta."
            )
        lab = scope.laboratory_of(request.user)
        if lab is None:
            raise PermissionDenied("Usuário sem laboratório vinculado.")
        return role, lab

    def create(self, request):
        role, lab = self._manager_lab(request)
        kind = request.data.get("kind")
        if role == "reseller" and kind != PointKind.PHARMACY:
            raise PermissionDenied(
                "Revendedor somente cria pontos de farmácia da própria rede."
            )
        ser = self.serializer_class(data=request.data, context={"laboratory": lab})
        ser.is_valid(raise_exception=True)
        point = ser.save(laboratory=lab, is_open=False)
        return Response(self.serializer_class(point).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        role, lab = self._manager_lab(request)
        point = self.get_queryset().filter(pk=pk).first()
        if point is None or point.laboratory_id != lab.pk:
            raise PermissionDenied()
        if role == "reseller" and point.kind != PointKind.PHARMACY:
            raise PermissionDenied("Revendedor só edita pontos de farmácia.")
        ser = self.serializer_class(
            point, data=request.data, partial=True, context={"laboratory": lab}
        )
        ser.is_valid(raise_exception=True)
        point = ser.save()
        return Response(self.serializer_class(point).data)

    # ---------- Janelas de horário ----------

    def add_window(self, request, pk=None):
        point = self._managed_point(request, pk)
        ser = OpeningWindowSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        OpeningWindow.objects.create(point=point, **ser.validated_data)
        return Response(
            self.serializer_class(point).data, status=status.HTTP_201_CREATED
        )

    def remove_window(self, request, pk=None, window_pk=None):
        point = self._managed_point(request, pk)
        removed = point.windows.filter(pk=window_pk).delete()[0]
        if not removed:
            raise PermissionDenied()
        return Response(self.serializer_class(point).data)

    def _managed_point(self, request, pk):
        role, lab = self._manager_lab(request)
        point = self.get_queryset().filter(pk=pk).first()
        if point is None or point.laboratory_id != lab.pk:
            raise PermissionDenied()
        if role == "reseller" and point.kind != PointKind.PHARMACY:
            raise PermissionDenied("Revendedor só gerencia pontos de farmácia.")
        return point

    # ---------- Designação de técnico (somente laboratório) ----------

    def assign_technician(self, request, pk=None):
        if request.user.role_code != rbac.LABORATORY:
            raise PermissionDenied("Somente o laboratório designa técnicos ao ponto.")
        lab = scope.laboratory_of(request.user)
        point = self.get_queryset().filter(pk=pk, laboratory=lab).first()
        if point is None:
            raise PermissionDenied()
        from apps.technicians.models import Technician

        technician = Technician.objects.filter(
            laboratory=lab, pk=request.data.get("technician_id")
        ).first()
        if technician is None:
            return Response(
                {
                    "error": {
                        "code": "invalid",
                        "message": "Técnico não pertence à rede.",
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        assignment, created = TechnicianAssignment.objects.get_or_create(
            point=point,
            technician=technician,
            defaults={"assigned_by": request.user, "active": True},
        )
        if not created and not assignment.active:
            assignment.active = True
            assignment.save(update_fields=["active", "updated_at"])
        return Response(self.serializer_class(point).data)

    def unassign_technician(self, request, pk=None, technician_pk=None):
        if request.user.role_code != rbac.LABORATORY:
            raise PermissionDenied("Somente o laboratório designa técnicos ao ponto.")
        lab = scope.laboratory_of(request.user)
        point = self.get_queryset().filter(pk=pk, laboratory=lab).first()
        if point is None:
            raise PermissionDenied()
        assignment = TechnicianAssignment.objects.filter(
            point=point, technician_id=technician_pk
        ).first()
        if assignment is None:
            raise PermissionDenied()
        assignment.active = False
        assignment.save(update_fields=["active", "updated_at"])
        return Response(self.serializer_class(point).data)

    # ---------- Operação: abrir/fechar pelo técnico designado ----------

    def open(self, request, pk=None):
        return self._operate(request, pk, opening=True)

    def close(self, request, pk=None):
        return self._operate(request, pk, opening=False)

    def _operate(self, request, pk, *, opening):
        point = CollectionPoint.objects.filter(pk=pk).first()
        if point is None:
            raise PermissionDenied()
        if request.user.role_code != rbac.TECHNICIAN:
            raise PermissionDenied("Somente o técnico designado opera o ponto.")
        technician = getattr(request.user, "technician_profile", None)
        if technician is None or not services.is_assigned(point, technician):
            raise PermissionDenied("Técnico não está designado a este ponto.")
        try:
            if opening:
                services.open_point(point, technician=technician, by_user=request.user)
            else:
                services.close_point(point, technician=technician, by_user=request.user)
        except services.CollectionPointError as exc:
            return Response(
                {
                    "error": {
                        "code": "collection_point_state",
                        "message": str(exc),
                        "details": {},
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(self.serializer_class(point).data)
