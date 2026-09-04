"""Consulta da trilha de auditoria (doc 11 §5), escopada por laboratório.

Superusuário vê tudo; usuários com permissão audit.view (laboratório) veem
apenas os eventos do próprio laboratório (atribuição em AuditLog.laboratory,
v1.1.9).
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
        "laboratory": (
            {"id": row.laboratory.pk, "name": row.laboratory.name}
            if row.laboratory_id
            else None
        ),
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
        from apps.accounts import rbac
        from apps.organizations import scope

        is_super = request.user.is_superuser
        if not is_super and not rbac.has_permission(request.user, "audit.view"):
            raise PermissionDenied("Sem permissão para consultar auditoria.")
        lab = None
        if not is_super:
            lab = scope.laboratory_of(request.user)
            if lab is None:
                raise PermissionDenied(
                    "Laboratório sem escopo: auditoria disponível para superusuário "
                    "ou laboratório com organização vinculada."
                )
        qs = AuditLog.objects.select_related("user", "laboratory").all()
        if lab is not None:
            qs = qs.filter(laboratory=lab)
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
