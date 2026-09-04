"""Endpoints de resultado de exame (D-06/D-07).

- Laboratório cadastra a URL externa do resultado e publica;
- publicação gera token de acesso (capability) para JSON e PÁGINA pública.
"""
import html

from django.core.validators import URLValidator
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts import rbac
from apps.audit.models import record as audit_record
from apps.organizations import scope
from apps.quotations.models import QuotationType
from apps.requests.models import CollectionRequest, ExamResult

_url_validator = URLValidator(schemes=["http", "https"])


def _json_payload(result, *, public=False):
    request_obj = result.request
    lab_name = request_obj.laboratory.name if request_obj.laboratory_id else None
    items = []
    final = (
        request_obj.quotations.filter(quotation_type=QuotationType.FINAL)
        .order_by("-version")
        .first()
    )
    if final is not None:
        items = [
            it.description or (it.exam.name if it.exam else "")
            for it in final.items.order_by("id")
        ]
    payload = {
        "id": result.pk,
        "protocol": request_obj.protocol,
        "laboratory": lab_name,
        "result_url": result.result_url,
        "note": result.note,
        "published": result.published,
        "published_at": result.published_at.isoformat() if result.published_at else None,
        "exams": [it for it in items if it],
    }
    if not public:
        payload["token"] = result.token
        payload["page_url"] = result.page_url()
    return payload


class RequestResultsView(APIView):
    """GET/POST /requests/{pk}/results — listar (escopo) e registrar (laboratório)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        req = CollectionRequest.objects.filter(pk=pk).first()
        if req is None or not self._can(request.user, req):
            raise PermissionDenied()
        rows = req.exam_results.order_by("-created_at")
        return Response([_json_payload(r) for r in rows])

    def post(self, request, pk=None):
        lab = scope.laboratory_of(request.user)
        if lab is None:
            raise PermissionDenied("Somente laboratório registra resultados.")
        req = CollectionRequest.objects.filter(pk=pk).first()
        if req is None:
            raise PermissionDenied()
        if req.laboratory_id is None:
            req.laboratory = lab
            req.save(update_fields=["laboratory", "updated_at"])
        elif req.laboratory_id != lab.pk:
            raise PermissionDenied("Solicitação fora da rede do laboratório.")
        result_url = str(request.data.get("result_url") or "").strip()
        if not result_url:
            raise ValidationError({"result_url": "Informe a URL com o resultado."})
        try:
            _url_validator(result_url)
        except Exception as exc:  # noqa: BLE001 — URL inválida
            raise ValidationError({"result_url": "URL inválida (http/https)."}) from exc
        note = str(request.data.get("note") or "").strip()
        result = ExamResult.objects.create(
            request=req, result_url=result_url, note=note, created_by=request.user
        )
        audit_record(
            action="exam_result.created",
            entity_type="requests.ExamResult",
            entity_id=result.pk,
            user=request.user,
            metadata={"protocol": req.protocol, "result_url": result_url},
        )
        return Response(_json_payload(result), status=status.HTTP_201_CREATED)

    @staticmethod
    def _can(user, req):
        if user.is_superuser:
            return True
        if user.role_code == rbac.PATIENT:
            return req.patient.user_id == user.pk
        lab = scope.laboratory_of(user)
        return lab is not None and req.laboratory_id == lab.pk


class ResultPublishView(APIView):
    """POST /results/{pk}/publish — laboratório publica e libera a página."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        result = ExamResult.objects.select_related("request").filter(pk=pk).first()
        if result is None:
            raise PermissionDenied()
        lab = scope.laboratory_of(request.user)
        if lab is None or result.request.laboratory_id != lab.pk:
            raise PermissionDenied("Somente o laboratório da solicitação publica resultados.")
        if not result.published:
            result.published = True
            result.published_at = timezone.now()
            result.published_by = request.user
            result.save(update_fields=["published", "published_at", "published_by", "updated_at"])
            audit_record(
                action="exam_result.published",
                entity_type="requests.ExamResult",
                entity_id=result.pk,
                user=request.user,
                metadata={"protocol": result.request.protocol, "token": result.token},
            )
        return Response(_json_payload(result))


class PublicResultView(APIView):
    """GET /results/{token} — JSON público do resultado publicado (capability)."""

    permission_classes = [AllowAny]

    def get(self, request, token=None):
        result = (
            ExamResult.objects.select_related("request__laboratory", "request__patient")
            .filter(token=token, published=True)
            .first()
        )
        if result is None:
            return Response(
                {
                    "error": {
                        "code": "not_found",
                        "message": "Resultado não encontrado.",
                        "details": {},
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(_json_payload(result, public=True))


class PublicResultPageView(APIView):
    """GET /results/{token}/page — página pública (HTML) com o resultado."""

    permission_classes = [AllowAny]

    def get(self, request, token=None):
        from django.http import HttpResponse

        result = (
            ExamResult.objects.select_related("request__laboratory")
            .filter(token=token, published=True)
            .first()
        )
        if result is None:
            return HttpResponse(
                "<h1>Resultado não encontrado ou ainda não publicado.</h1>", status=404
            )
        req = result.request
        lab_name = req.laboratory.name if req.laboratory_id else ""
        external = result.result_url
        published_txt = (
            result.published_at.strftime("%d/%m/%Y %H:%M")
            if result.published_at
            else ""
        )
        protocol = html.escape(req.protocol)
        note = html.escape(result.note)
        lab_esc = html.escape(lab_name)
        link_esc = html.escape(external)
        css = (
            "<style>body{font-family:system-ui,sans-serif;max-width:640px;"
            "margin:40px auto;padding:0 16px;color:#1f2937}"
            ".card{border:1px solid #e5e7eb;border-radius:12px;padding:20px}"
            "h1{font-size:20px}.meta{color:#6b7280;font-size:14px}"
            "a{color:#047857}</style>"
        )
        body = (
            "<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>"
            f"<title>Resultado — {protocol}</title>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"{css}</head><body><div class='card'>"
            f"<h1>Resultado de exame — {protocol}</h1>"
            f"<p class='meta'>{lab_esc}</p>"
            f"<p class='meta'>Publicado em {published_txt}</p>"
            f"<p><a href='{link_esc}' target='_blank' rel='noopener'>"
            "Abrir resultado do exame ↗</a></p>"
            f"<p class='meta'>{note}</p></div></body></html>"
        )
        return HttpResponse(body, content_type="text/html; charset=utf-8")
