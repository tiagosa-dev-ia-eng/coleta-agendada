"""Endpoints do canal WhatsApp (doc 07 §10) — provider simulator até G-05."""
from django.conf import settings
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.accounts import rbac
from apps.organizations import scope
from apps.whatsapp.models import WhatsAppConversation
from apps.whatsapp.services import WhatsAppService, normalize_phone


def _can_view_conversation(user, conv):
    if user.is_superuser:
        return True
    if user.role_code == rbac.PATIENT:
        prof = getattr(user, "patient_profile", None)
        return prof is not None and conv.patient_id == prof.pk
    lab = scope.laboratory_of(user)
    return lab is not None and conv.laboratory_id == lab.pk


class InboundWhatsAppView(APIView):
    """POST /webhooks/whatsapp — recebe mensagem do canal (ou do simulador)."""

    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        secret = getattr(settings, "WHATSAPP_WEBHOOK_SECRET", "")
        if secret and request.headers.get("X-Webhook-Secret", "") != secret:
            raise PermissionDenied("Webhook não autorizado.")
        from_field = request.data.get("from")
        body = request.data.get("body")
        if not from_field or not body:
            return Response(
                {
                    "error": {
                        "code": "invalid",
                        "message": "Campos 'from' e 'body' são obrigatórios.",
                        "details": {},
                    }
                },
                status=400,
            )
        try:
            conv = WhatsAppService.handle_inbound(
                {
                    "from": from_field,
                    "body": body,
                    "message_id": request.data.get("message_id"),
                    "provider": request.data.get("provider") or settings.WHATSAPP_PROVIDER,
                },
                request=request,
            )
        except ValueError as exc:
            return Response(
                {"error": {"code": "invalid", "message": str(exc), "details": {}}},
                status=400,
            )
        return Response({"status": "ok", "conversation_id": conv.pk, "provider": conv.provider})


class ConversationByPhoneView(APIView):
    """GET /whatsapp/conversations/by-phone/{phone} — conversa + mensagens."""

    permission_classes = [IsAuthenticated]

    def get(self, request, phone):
        conv = WhatsAppConversation.objects.filter(
            phone=normalize_phone(phone)
        ).first()
        if conv is None or not _can_view_conversation(request.user, conv):
            raise PermissionDenied()
        messages = [
            {
                "id": m.pk,
                "direction": m.direction,
                "content": m.content,
                "ai_interpretation": m.ai_interpretation,
                "ai_model": m.ai_model,
                "ai_used_mock": m.ai_used_mock,
                "created_at": m.created_at.isoformat(),
            }
            for m in conv.messages.all()
        ]
        return Response(
            {
                "id": conv.pk,
                "phone": conv.phone,
                "provider": conv.provider,
                "status": conv.status,
                "patient": (
                    {"id": conv.patient_id, "email": conv.patient.user.email}
                    if conv.patient_id
                    else None
                ),
                "laboratory": conv.laboratory.name if conv.laboratory_id else None,
                "messages": messages,
            }
        )


class ConversationListView(APIView):
    """GET /whatsapp/conversations — conversas do laboratório (escopo)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.is_superuser or user.role_code == rbac.LABORATORY:
            lab = scope.laboratory_of(user)
            qs = (
                WhatsAppConversation.objects.filter(laboratory=lab)
                if lab
                else WhatsAppConversation.objects.none()
            )
        elif user.role_code == rbac.PATIENT:
            prof = getattr(user, "patient_profile", None)
            qs = (
                WhatsAppConversation.objects.filter(patient=prof)
                if prof
                else WhatsAppConversation.objects.none()
            )
        else:
            qs = WhatsAppConversation.objects.none()
        return Response(
            [
                {
                    "id": c.pk,
                    "phone": c.phone,
                    "provider": c.provider,
                    "status": c.status,
                    "patient_email": c.patient.user.email if c.patient_id else None,
                    "updated_at": c.updated_at.isoformat(),
                }
                for c in qs
            ]
        )
