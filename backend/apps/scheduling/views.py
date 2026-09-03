"""Endpoints de agendamento (doc 07 §6) e agenda por perfil (doc 04 §2)."""
from django.db import models
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts import rbac
from apps.organizations import scope
from apps.requests.models import CollectionRequest
from apps.scheduling.models import Appointment
from apps.scheduling.serializers import AppointmentReadSerializer, AppointmentWriteSerializer
from apps.scheduling.services import AppointmentService


def _visible(user):
    """Agenda conforme o perfil (doc 04 §2): cada um vê apenas a sua operação."""
    qs = Appointment.objects.select_related(
        "request__patient__user", "laboratory", "pharmacy", "technician__user"
    )
    role = user.role_code
    if user.is_superuser or role == rbac.LABORATORY:
        lab = scope.laboratory_of(user)
        return qs.filter(laboratory=lab) if lab else qs.none()
    if role == rbac.PATIENT:
        return qs.filter(request__patient__user=user)
    if role == rbac.PHARMACY:
        prof = getattr(user, "pharmacy_profile", None)
        return qs.filter(pharmacy=prof) if prof else qs.none()
    if role == rbac.TECHNICIAN:
        prof = getattr(user, "technician_profile", None)
        return qs.filter(technician=prof) if prof else qs.none()
    if role == rbac.RESELLER:
        prof = getattr(user, "reseller_profile", None)
        if prof is None:
            return qs.none()
        return qs.filter(
            models.Q(pharmacy__reseller=prof) | models.Q(technician__reseller=prof)
        )
    return qs.none()


def _can_execute(user, appt):
    """Execução da coleta: técnico atribuído ou laboratório."""
    if user.is_superuser or user.role_code == rbac.LABORATORY:
        return True
    if user.role_code == rbac.TECHNICIAN:
        prof = getattr(user, "technician_profile", None)
        return prof is not None and appt.technician_id == prof.pk
    return False


class ScheduleAppointmentView(APIView):
    """POST /requests/{pk}/appointment — laboratório agenda a coleta aprovada."""

    def post(self, request, pk=None):
        req = CollectionRequest.objects.select_related("patient__user").filter(pk=pk).first()
        if req is None:
            raise PermissionDenied()
        if request.user.role_code != rbac.LABORATORY:
            raise PermissionDenied("Somente o laboratório pode agendar.")
        lab = scope.laboratory_of(request.user)
        if lab is None:
            raise PermissionDenied("Usuário sem laboratório vinculado.")
        if req.laboratory_id is None:
            req.laboratory = lab
            req.save(update_fields=["laboratory", "updated_at"])
        elif req.laboratory_id != lab.pk:
            raise PermissionDenied("Solicitação pertence a outro laboratório.")
        ser = AppointmentWriteSerializer(data=request.data, context={"laboratory": lab})
        ser.is_valid(raise_exception=True)
        appt = AppointmentService.schedule(
            req,
            lab=lab,
            mode=ser.validated_data["mode"],
            scheduled_at=ser.validated_data["scheduled_at"],
            pharmacy=ser.validated_data.get("pharmacy"),
            technician=ser.validated_data.get("technician"),
            location_label=ser.validated_data.get("location_label", ""),
            created_by=request.user,
        )
        return Response(
            AppointmentReadSerializer(appt).data, status=status.HTTP_201_CREATED
        )


class AppointmentListView(APIView):
    """GET /appointments — agenda escopada por perfil (doc 04 §2)."""

    def get(self, request):
        qs = _visible(request.user)
        if request.query_params.get("upcoming") == "true":
            qs = qs.filter(scheduled_at__gte=timezone.now())
        return Response(AppointmentReadSerializer(qs, many=True).data)


class AppointmentDetailView(APIView):
    def get(self, request, pk=None):
        appt = Appointment.objects.filter(pk=pk).first()
        if appt is None or appt not in _visible(request.user):
            raise PermissionDenied()
        return Response(AppointmentReadSerializer(appt).data)


class AppointmentCheckinView(APIView):
    """RF-013: check-in do técnico (SCHEDULED -> IN_PROGRESS)."""

    def post(self, request, pk=None):
        appt = Appointment.objects.filter(pk=pk).first()
        if appt is None or not _can_execute(request.user, appt):
            raise PermissionDenied()
        AppointmentService.check_in(appt, performed_by=request.user, request=request)
        return Response(AppointmentReadSerializer(appt).data)


class AppointmentCheckoutView(APIView):
    def post(self, request, pk=None):
        appt = Appointment.objects.filter(pk=pk).first()
        if appt is None or not _can_execute(request.user, appt):
            raise PermissionDenied()
        AppointmentService.check_out(appt, performed_by=request.user, request=request)
        return Response(AppointmentReadSerializer(appt).data)


class AppointmentCompleteView(APIView):
    """CT-INT-005: concluir a coleta NÃO depende de pagamento (ADR-008)."""

    def post(self, request, pk=None):
        appt = Appointment.objects.filter(pk=pk).first()
        if appt is None or not _can_execute(request.user, appt):
            raise PermissionDenied()
        AppointmentService.complete(appt, performed_by=request.user, request=request)
        return Response(AppointmentReadSerializer(appt).data)
