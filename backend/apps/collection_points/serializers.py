"""Serializers do Local de Coleta (D-03) — criação/edição e leitura."""
from rest_framework import serializers

from apps.collection_points.models import CollectionPoint, OpeningWindow, PointKind
from apps.organizations.models import Pharmacy


class OpeningWindowSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpeningWindow
        fields = ["id", "weekday", "open_time", "close_time"]
        read_only_fields = ["id"]


class CollectionPointSerializer(serializers.ModelSerializer):
    pharmacy = serializers.PrimaryKeyRelatedField(
        queryset=Pharmacy.objects.select_related("laboratory").all(),
        required=False,
        allow_null=True,
        default=None,
    )
    pharmacy_name = serializers.CharField(source="pharmacy.name", read_only=True)
    windows = OpeningWindowSerializer(many=True, read_only=True)
    technicians = serializers.SerializerMethodField()
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = CollectionPoint
        fields = [
            "id",
            "kind",
            "kind_display",
            "laboratory",
            "pharmacy",
            "pharmacy_name",
            "name",
            "address",
            "city",
            "state",
            "zip_code",
            "latitude",
            "longitude",
            "is_open",
            "status",
            "windows",
            "technicians",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "laboratory",
            "is_open",
            "created_at",
            "updated_at",
            "windows",
            "technicians",
        ]

    def get_technicians(self, obj):
        return [
            {
                "id": a.technician_id,
                "email": a.technician.user.email,
                "active": a.active,
                "assigned_at": a.created_at.isoformat(),
            }
            for a in obj.technician_assignments.select_related("technician__user")
        ]

    def validate_kind(self, value):
        if self.instance is not None and self.instance.kind != value:
            raise serializers.ValidationError("O tipo do ponto de coleta não pode mudar.")
        return value

    def validate(self, attrs):
        laboratory = self.context.get("laboratory")
        kind = attrs.get("kind", getattr(self.instance, "kind", None) if self.instance else None)
        pharmacy = attrs.get(
            "pharmacy",
            getattr(self.instance, "pharmacy", None) if self.instance else None,
        )
        if kind not in PointKind.values:
            raise serializers.ValidationError({"kind": "Tipo de ponto inválido."})
        if kind == PointKind.PHARMACY:
            if pharmacy is None:
                raise serializers.ValidationError(
                    {"pharmacy": "Ponto de farmácia exige pharmacy_id."}
                )
            if laboratory is not None and pharmacy.laboratory_id != laboratory.pk:
                raise serializers.ValidationError(
                    {"pharmacy": "Farmácia não pertence à rede deste laboratório."}
                )
        else:
            if attrs.get("pharmacy") is not None:
                raise serializers.ValidationError(
                    {"pharmacy": "Ponto de laboratório não pode ter farmácia anfitriã."}
                )
            attrs["pharmacy"] = None
        # um mesmo host só pode ter um ponto (constraint uniq_pharmacy_hosted_point)
        if (
            kind == PointKind.PHARMACY
            and pharmacy is not None
            and CollectionPoint.objects.filter(kind=PointKind.PHARMACY, pharmacy=pharmacy)
            .exclude(pk=getattr(self.instance, "pk", None))
            .exists()
        ):
            raise serializers.ValidationError(
                {"pharmacy": "Esta farmácia já é um ponto de coleta."}
            )
        return attrs
