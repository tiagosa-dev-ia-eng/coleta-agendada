"""Consulta da trilha de auditoria (doc 11 §5).

Segurança (menor privilégio): endpoint restrito a SUPERUSUÁRIO nesta versão.
A permissão 'audit.view' existe no catálogo para laboratório; escopo por
laboratório exige atribuir o laboratório no AuditLog — evolução registrada.
"""
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditLog


def _serialize(row):
    return {
        "id": row.pk,
        "action": row.action,
        "entity_type": row.entity_type,
        "entity_id": row.entity_id,
        "user": (
            {"id": row.user.pk, "email": row.user.email}
            if row.user_id
            else None
        ),
        "ip": row.ip,
        "metadata": row.metadata,
        "created_at": row.created_at.isoformat(),
    }


class AuditLogListView(APIView):
    """GET /audit — lista a trilha com filtros (somente superusuário)."""

    def get(self, request):
        if not request.user.is_superuser:
            raise PermissionDenied("Somente superusuário consulta auditoria.")
        qs = AuditLog.objects.select_related("user").all()
        params = request.query_params
        if params.get("action"):
            qs = qs.filter(action__iexact=params["action"])
        if params.get("entity_type"):
            qs = qs.filter(entity_type__iexact=params["entity_type"])
        if params.get("entity_id"):
            qs = qs.filter(entity_id=str(params["entity_id"]))
        if params.get("user_id"):
            qs = qs.filter(user_id=params["user_id"])
        start = parse_datetime(params["start"]) if params.get("start") else None
        end = parse_datetime(params["end"]) if params.get("end") else None
        if start:
            qs = qs.filter(created_at__gte=start)
        if end:
            qs = qs.filter(created_at__lte=end)
        try:
            limit = min(int(params.get("limit", "100")), 200)
        except ValueError:
            limit = 100
        qs = qs.order_by("-created_at")[:limit]
        return Response(
            {
                "count": AuditLog.objects.count(),
                "items": [_serialize(row) for row in qs],
            }
        )
