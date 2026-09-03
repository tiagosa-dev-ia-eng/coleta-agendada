from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts import rbac
from apps.accounts.views import permission_required
from apps.patients.models import Patient
from apps.patients.serializers import PatientCreateSerializer


class PatientViewSet(viewsets.GenericViewSet):
    """Pacientes: gestão administrativa (user.manage); paciente vê o próprio perfil."""

    serializer_class = PatientCreateSerializer

    def get_queryset(self):
        return Patient.objects.select_related("user").order_by("-created_at")

    def get_permissions(self):
        if self.action in ("list", "create", "partial_update", "update"):
            return [IsAuthenticated(), permission_required("user.manage")()]
        return [IsAuthenticated()]

    def list(self, request):
        qs = self.get_queryset()
        return Response(self.serializer_class(qs, many=True).data)

    def retrieve(self, request, pk=None):
        patient = Patient.objects.filter(pk=pk).first()
        own = (
            request.user.role_code == rbac.PATIENT
            and getattr(request.user, "patient_profile", None) is not None
            and patient is not None
            and request.user.patient_profile.pk == patient.pk
        )
        if patient is None or not (rbac.has_permission(request.user, "user.manage") or own):
            raise PermissionDenied()
        return Response(self.serializer_class(patient).data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        patient = serializer.save()
        return Response(self.serializer_class(patient).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        patient = self.get_queryset().filter(pk=pk).first()
        if patient is None:
            raise PermissionDenied()
        serializer = self.serializer_class(patient, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        patient = serializer.save()
        return Response(self.serializer_class(patient).data)
