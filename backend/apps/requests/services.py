"""Serviços de domínio de solicitações (regra 5 do AGENTS.md)."""
import logging

from rest_framework.exceptions import APIException

from apps.audit.models import record as audit_record
from apps.requests.models import RequestStatusHistory
from apps.requests.statuses import RequestStatus, valid_from

logger = logging.getLogger(__name__)


class InvalidTransition(APIException):
    """Transição de estado não permitida pela máquina de estados (doc 05)."""

    status_code = 409
    default_code = "invalid_transition"
    default_detail = "Transição de estado não permitida para esta solicitação."


class RequestStateService:
    """Único ponto autorizado a mudar o status de uma CollectionRequest."""

    @staticmethod
    def mark_created(request, *, changed_by=None, origin="system"):
        """Registra a criação (REQUESTED) no histórico — sem transição de estado."""
        RequestStatusHistory.objects.create(
            request=request,
            from_status=RequestStatus.REQUESTED,
            to_status=RequestStatus.REQUESTED,
            changed_by=changed_by,
            origin=origin,
            reason="Solicitação criada",
        )
        audit_record(
            action="request.created",
            entity_type="requests.CollectionRequest",
            entity_id=request.pk,
            user=changed_by,
            metadata={"protocol": request.protocol, "origin": origin},
        )

    @staticmethod
    def transition(
        request,
        to_status,
        *,
        changed_by=None,
        origin="system",
        reason="",
        metadata=None,
    ):
        """Valida e executa uma transição; grava histórico e auditoria."""
        to_status = str(to_status)
        from_status = request.status
        allowed = valid_from(request.status)
        if to_status not in {str(s) for s in allowed}:
            raise InvalidTransition(
                detail=(
                    f"Transição {from_status} -> {to_status} não permitida "
                    f"(permitidas: {sorted(str(s) for s in allowed) or 'nenhuma'})."
                )
            )
        request.status = to_status
        request.save(update_fields=["status", "updated_at"])
        RequestStatusHistory.objects.create(
            request=request,
            from_status=from_status,
            to_status=to_status,
            changed_by=changed_by,
            origin=origin,
            reason=reason,
            metadata=metadata or {},
        )
        audit_record(
            action="request.status_changed",
            entity_type="requests.CollectionRequest",
            entity_id=request.pk,
            user=changed_by,
            metadata={
                "protocol": request.protocol,
                "from_status": from_status,
                "to_status": to_status,
                "origin": origin,
                "reason": reason,
            },
        )
        return request

    @staticmethod
    def cancel(request, *, changed_by=None, origin="system", reason=""):
        """Cancelamento: permitido enquanto não terminal/não agendado."""
        allowed = valid_from(request.status)
        if RequestStatus.CANCELED not in allowed:
            raise InvalidTransition(
                detail=f"Solicitação {request.status} não pode ser cancelada."
            )
        return RequestStateService.transition(
            request,
            RequestStatus.CANCELED,
            changed_by=changed_by,
            origin=origin,
            reason=reason,
        )
