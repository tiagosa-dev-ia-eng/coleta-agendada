"""AppointmentService — agendamento e execução da coleta (docs 05/10, ADR-008)."""
from django.utils import timezone
from rest_framework.exceptions import APIException

from apps.audit.models import record as audit_record
from apps.requests.services import RequestStateService
from apps.requests.statuses import RequestStatus
from apps.scheduling.models import Appointment, AppointmentMode


class SchedulingError(APIException):
    status_code = 409
    default_code = "scheduling_error"
    default_detail = "Operação inválida para este agendamento."


class AppointmentExists(SchedulingError):
    default_code = "appointment_exists"
    default_detail = "Esta solicitação já possui agendamento."


def _audit(request, action, entity, metadata=None):
    audit_record(
        action=action,
        entity_type="scheduling.Appointment",
        entity_id=entity.pk,
        user=getattr(request, "user", None),
        ip=request.META.get("REMOTE_ADDR") if request is not None else None,
        user_agent=request.META.get("HTTP_USER_AGENT", "") if request is not None else "",
        metadata=metadata or {},
    )


class AppointmentService:
    @staticmethod
    def schedule(request_obj, *, lab, mode, scheduled_at, pharmacy=None, technician=None,
                 location_label="", created_by=None):
        """Cria o agendamento (APROVADO -> AGENDADO) — RF-010/011."""
        from apps.scheduling.models import Appointment as _Appt

        if _Appt.objects.filter(request=request_obj).exists():
            raise AppointmentExists()
        if request_obj.status != RequestStatus.APPROVED:
            raise SchedulingError(
                detail="Somente solicitações APROVADAS podem ser agendadas."
            )
        if mode == AppointmentMode.PHARMACY and pharmacy is None:
            raise SchedulingError(detail="Modalidade farmácia exige pharmacy_id.")
        if mode == AppointmentMode.DOMICILIARY and technician is None:
            raise SchedulingError(detail="Modalidade domiciliar exige technician_id.")
        point = AppointmentService._resolve_point(lab, mode, scheduled_at, pharmacy)
        if mode != AppointmentMode.DOMICILIARY and point is None:
            label = (
                "A farmácia informada"
                if mode == AppointmentMode.PHARMACY
                else "A unidade do laboratório"
            )
            raise SchedulingError(detail=f"{label} não é um ponto de coleta ativo.")
        appt = Appointment.objects.create(
            request=request_obj,
            mode=mode,
            laboratory=lab,
            pharmacy=pharmacy,
            technician=technician,
            scheduled_at=scheduled_at,
            location_label=location_label,
            created_by=created_by,
        )
        RequestStateService.transition(
            request_obj,
            RequestStatus.SCHEDULED,
            changed_by=created_by,
            origin="user",
            reason="Agendamento confirmado (protocolo, data, horário e local).",
        )
        audit_record(
            action="appointment.scheduled",
            entity_type="scheduling.Appointment",
            entity_id=appt.pk,
            user=created_by,
            metadata={
                "protocol": request_obj.protocol,
                "code": appt.code,
                "mode": mode,
                "scheduled_at": scheduled_at.isoformat(),
            },
        )
        return appt

    @staticmethod
    def _resolve_point(lab, mode, scheduled_at, pharmacy=None):
        """Ponto de coleta válido para o agendamento (D-03).

        Modalidades em ponto (pharmacy/laboratory) exigem ponto ATIVO e
        disponibilidade no horário (janelas semanais + fechado hoje). Retorna
        o ponto escolhido ou None quando não há candidato ativo; levanta
        SchedulingError quando existe ponto mas sem disponibilidade.
        """
        from apps.collection_points import services as point_services
        from apps.collection_points.models import CollectionPoint, PointKind

        if mode == AppointmentMode.DOMICILIARY:
            return None
        qs = CollectionPoint.objects.filter(laboratory=lab, status="active")
        if mode == AppointmentMode.PHARMACY:
            qs = qs.filter(kind=PointKind.PHARMACY, pharmacy=pharmacy)
        else:
            qs = qs.filter(kind=PointKind.LABORATORY)
        candidates = list(qs.order_by("name"))
        if not candidates:
            return None
        last_error = None
        for point in candidates:
            try:
                point_services.check_schedule_availability(point, scheduled_at)
                return point
            except point_services.CollectionPointError as exc:
                last_error = exc
        if last_error is not None:
            raise SchedulingError(detail=str(last_error))
        raise SchedulingError(detail="Sem disponibilidade no horário solicitado.")

    @staticmethod
    def check_in(appt, *, performed_by, request=None):
        """RF-013: técnico inicia a realização (SCHEDULED -> IN_PROGRESS)."""
        if appt.request.status == RequestStatus.IN_PROGRESS and appt.checkin_at:
            return appt  # idempotente
        if appt.request.status != RequestStatus.SCHEDULED:
            raise SchedulingError(detail="Agendamento não está pronto para check-in.")
        appt.checkin_at = timezone.now()
        appt.save(update_fields=["checkin_at", "updated_at"])
        RequestStateService.transition(
            appt.request,
            RequestStatus.IN_PROGRESS,
            changed_by=performed_by,
            origin="user",
            reason="Check-in do técnico",
        )
        _audit(request or performed_by, "appointment.checkin", appt)
        return appt

    @staticmethod
    def check_out(appt, *, performed_by, request=None):
        if not appt.checkin_at:
            raise SchedulingError(detail="Check-in ainda não realizado.")
        if appt.checkout_at:
            return appt
        appt.checkout_at = timezone.now()
        appt.save(update_fields=["checkout_at", "updated_at"])
        _audit(request or performed_by, "appointment.checkout", appt)
        return appt

    @staticmethod
    def complete(appt, *, performed_by, request=None):
        """RF-012: concluir coleta. NÃO exige pagamento (ADR-008 / CT-INT-005)."""
        from apps.requests.statuses import RequestStatus as RS

        if appt.request.status == RS.COMPLETED and appt.completed_at:
            return appt  # idempotente
        current = appt.request.status
        if current not in (RS.SCHEDULED, RS.IN_PROGRESS):
            raise SchedulingError(detail="Agendamento não está em execução.")
        if current == RS.SCHEDULED:
            RequestStateService.transition(
                appt.request,
                RS.IN_PROGRESS,
                changed_by=performed_by,
                origin="user",
                reason="Início da realização",
            )
        RequestStateService.transition(
            appt.request,
            RS.COMPLETED,
            changed_by=performed_by,
            origin="user",
            reason="Coleta realizada (pagamento não bloqueia — ADR-008)",
        )
        if not appt.checkin_at:
            appt.checkin_at = timezone.now()
        appt.completed_at = timezone.now()
        appt.save(update_fields=["checkin_at", "completed_at", "updated_at"])
        _audit(request or performed_by, "appointment.completed", appt)
        # G-03: comissões FIXAS geram na conclusão (não bloqueiam a coleta)
        from apps.commissions.services import trigger_fixed_on_completion

        trigger_fixed_on_completion(appt.request)
        return appt
