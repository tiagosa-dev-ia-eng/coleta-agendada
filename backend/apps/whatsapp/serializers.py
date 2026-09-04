"""Serializer dos contatos WhatsApp por perfil (D-04)."""

from rest_framework import serializers

from apps.whatsapp.models import WhatsAppContact
from apps.whatsapp.validators import normalize_phone_digits


class WhatsAppContactSerializer(serializers.ModelSerializer):
    owner_kind = serializers.SerializerMethodField()

    class Meta:
        model = WhatsAppContact
        fields = [
            "id",
            "owner_kind",
            "pharmacy",
            "laboratory",
            "technician",
            "reseller",
            "number",
            "name",
            "meta_bsuid",
            "is_main",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner_kind", "created_at", "updated_at"]

    def get_owner_kind(self, obj):
        if obj.pharmacy_id:
            return "pharmacy"
        if obj.laboratory_id:
            return "laboratory"
        if obj.technician_id:
            return "technician"
        if obj.reseller_id:
            return "reseller"
        return None

    def validate(self, attrs):
        if self.instance is None:
            owners = [
                attrs.get("pharmacy"),
                attrs.get("laboratory"),
                attrs.get("technician"),
                attrs.get("reseller"),
            ]
            set_owners = [owner for owner in owners if owner is not None]
            if len(set_owners) != 1:
                raise serializers.ValidationError(
                    "Informe exatamente um dono: pharmacy, laboratory, technician ou reseller."
                )
            number = attrs.get("number")
            if number:
                attrs["number"] = normalize_phone_digits(number)
            if not attrs.get("number"):
                raise serializers.ValidationError(
                    {"number": "Número de WhatsApp inválido."}
                )
            return attrs
        # edição: dono é imutável (excluir via reatribuição)
        owner_keys = [
            key for key in ("pharmacy", "laboratory", "technician", "reseller")
            if key in attrs
        ]
        if owner_keys:
            raise serializers.ValidationError(
                "O dono do contato não pode ser alterado."
            )
        if "number" in attrs and attrs.get("number"):
            attrs["number"] = normalize_phone_digits(attrs["number"])
        return attrs
