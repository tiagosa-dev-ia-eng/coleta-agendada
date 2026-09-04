"""Endpoints de contatos WhatsApp por perfil (D-04 — BSUID Meta)."""
from django.db import models
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.accounts import rbac
from apps.organizations import scope
from apps.whatsapp.models import WhatsAppContact
from apps.whatsapp.serializers import WhatsAppContactSerializer


def _owner_visible_qs(user):
    """Contatos do perfil conforme escopo (doc 04)."""
    qs = WhatsAppContact.objects.select_related(
        "pharmacy", "laboratory", "technician__user", "reseller"
    ).all()
    role = user.role_code
    if user.is_superuser or role == rbac.LABORATORY:
        lab = scope.laboratory_of(user)
        return (
            qs.filter(
                models.Q(pharmacy__laboratory=lab)
                | models.Q(laboratory=lab)
                | models.Q(technician__laboratory=lab)
                | models.Q(reseller__laboratory=lab)
            )
            if lab
            else qs.none()
        )
    if role == rbac.RESELLER:
        prof = getattr(user, "reseller_profile", None)
        return (
            qs.filter(
                models.Q(pharmacy__reseller=prof)
                | models.Q(reseller=prof)
                | models.Q(technician__reseller=prof)
            )
            if prof
            else qs.none()
        )
    if role == rbac.PHARMACY:
        prof = getattr(user, "pharmacy_profile", None)
        return qs.filter(pharmacy=prof) if prof else qs.none()
    if role == rbac.TECHNICIAN:
        prof = getattr(user, "technician_profile", None)
        return qs.filter(technician=prof) if prof else qs.none()
    return qs.none()


class WhatsAppContactViewSet(GenericViewSet):
    serializer_class = WhatsAppContactSerializer
    queryset = WhatsAppContact.objects.none()

    def get_queryset(self):
        return _owner_visible_qs(self.request.user)

    def list(self, request):
        return Response(self.serializer_class(self.get_queryset(), many=True).data)

    def retrieve(self, request, pk=None):
        contact = self.get_queryset().filter(pk=pk).first()
        if contact is None:
            raise PermissionDenied()
        return Response(self.serializer_class(contact).data)

    def _owner_from_data(self, data):
        """Identifica o dono (PrimaryKeyRelatedField entrega a instância)."""
        technician = data.get("technician")
        reseller = data.get("reseller")
        laboratory = data.get("laboratory")
        pharmacy = data.get("pharmacy")
        if technician is not None:
            return "technician", technician, technician.laboratory
        if reseller is not None:
            return "reseller", reseller, reseller.laboratory
        if laboratory is not None:
            return "laboratory", laboratory, laboratory
        if pharmacy is not None:
            return "pharmacy", pharmacy, pharmacy.laboratory
        return None, None, None

    def _authorize_owner(self, user, kind, obj):
        """Autorização de criação do contato conforme o papel."""
        if obj is None:
            raise PermissionDenied("Dono do contato não encontrado.")
        role = user.role_code
        lab = scope.laboratory_of(user)
        if role == rbac.LABORATORY:
            if lab is None or kind == "laboratory":
                # ponto: laboratório só registra o próprio laboratório
                if kind == "laboratory" and obj.pk == (lab.pk if lab else None):
                    return
                raise PermissionDenied("Dono fora da rede deste laboratório.")
            owner_lab = obj.laboratory
            if owner_lab is None or owner_lab.pk != lab.pk:
                raise PermissionDenied("Dono fora da rede deste laboratório.")
            return
        if role == rbac.RESELLER:
            prof = getattr(user, "reseller_profile", None)
            allowed = prof is not None and (
                (kind == "pharmacy" and obj.reseller_id == prof.pk)
                or (kind == "technician" and obj.reseller_id == prof.pk)
                or (kind == "reseller" and obj.pk == prof.pk)
            )
            if not allowed:
                raise PermissionDenied("Revendedor só gerencia a própria rede.")
            return
        if role == rbac.PHARMACY and kind == "pharmacy":
            prof = getattr(user, "pharmacy_profile", None)
            if prof is not None and obj.pk == prof.pk:
                return
        if role == rbac.TECHNICIAN and kind == "technician":
            prof = getattr(user, "technician_profile", None)
            if prof is not None and obj.pk == prof.pk:
                return
        raise PermissionDenied("Sem permissão para este contato.")

    def create(self, request):
        ser = self.serializer_class(data=request.data)
        ser.is_valid(raise_exception=True)
        kind, obj, _ = self._owner_from_data(ser.validated_data)
        self._authorize_owner(request.user, kind, obj)
        # técnico e revenda: um único número (D-04)
        if kind in ("technician", "reseller") and WhatsAppContact.objects.filter(
            **{kind: obj}
        ).exists():
            return Response(
                {
                    "error": {
                        "code": "contact_limit",
                        "message": "Técnico/revenda possui um único contato WhatsApp.",
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        payload = {
            "number": ser.validated_data["number"],
            "name": ser.validated_data.get("name", ""),
            "meta_bsuid": ser.validated_data.get("meta_bsuid", ""),
            "is_main": ser.validated_data.get("is_main", False),
        }
        payload[kind] = obj
        contact = WhatsAppContact.objects.create(**payload)
        return Response(
            self.serializer_class(contact).data, status=status.HTTP_201_CREATED
        )

    def destroy(self, request, pk=None):
        contact = self.get_queryset().filter(pk=pk).first()
        if contact is None:
            raise PermissionDenied()
        contact.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
