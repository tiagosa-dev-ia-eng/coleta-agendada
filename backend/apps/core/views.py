"""Health checks: liveness (/health) e readiness (/ready) — doc 13 §8."""
import logging

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)

SERVICE = "coleta-agendada-api"


@require_GET
def health(request):
    """Liveness: o processo está de pé."""
    return JsonResponse({"status": "ok", "service": SERVICE})


@require_GET
def ready(request):
    """Readiness: dependências essenciais respondem (banco de dados)."""
    checks = {"database": "ok"}
    ok = True
    try:
        connection.ensure_connection()
    except Exception:  # noqa: BLE001 — qualquer falha de conexão derruba o ready
        logger.exception("Falha no health check de banco de dados")
        checks["database"] = "error"
        ok = False
    payload = {"status": "ok" if ok else "degraded", "checks": checks}
    return JsonResponse(payload, status=200 if ok else 503)



@require_GET
def version(request):
    """Versão interna do projeto (controle de versão — VERSION na raiz)."""
    import pathlib

    from django.conf import settings

    version_file = pathlib.Path(settings.BASE_DIR).parent / "VERSION"
    try:
        value = version_file.read_text(encoding="utf-8").strip()
    except OSError:
        value = "unknown"
    return JsonResponse({"name": SERVICE, "version": value})

