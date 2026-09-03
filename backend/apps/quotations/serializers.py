from rest_framework import serializers

from apps.quotations.models import Quotation


class QuotationItemSerializer(serializers.Serializer):
    """Item na saída."""

    id = serializers.IntegerField()
    exam = serializers.SerializerMethodField()
    description = serializers.CharField()
    quantity = serializers.IntegerField()
    unit_price = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    source = serializers.CharField()

    def get_exam(self, obj):
        if obj.exam_id is None:
            return None
        return {"id": obj.exam_id, "code": obj.exam.code, "name": obj.exam.name}

    def get_unit_price(self, obj):
        return str(obj.unit_price) if obj.unit_price is not None else None

    def get_total_price(self, obj):
        if obj.total_price is None:
            return None
        return str(obj.total_price)


class QuotationReadSerializer(serializers.ModelSerializer):
    request_protocol = serializers.CharField(source="request.protocol", read_only=True)
    quotation_type_display = serializers.CharField(
        source="get_quotation_type_display", read_only=True
    )
    is_final = serializers.BooleanField(read_only=True)
    is_validated = serializers.BooleanField(read_only=True)
    is_sent = serializers.BooleanField(read_only=True)
    is_approved = serializers.BooleanField(read_only=True)
    missing_price_count = serializers.IntegerField(read_only=True)
    validated_by_email = serializers.CharField(
        source="validated_by.email", read_only=True, default=None
    )
    items = serializers.SerializerMethodField()

    class Meta:
        model = Quotation
        fields = [
            "id",
            "request_id",
            "request_protocol",
            "version",
            "quotation_type",
            "quotation_type_display",
            "generated_by_ai",
            "notes",
            "subtotal",
            "total",
            "is_final",
            "is_validated",
            "is_sent",
            "is_approved",
            "missing_price_count",
            "validated_by_email",
            "validated_at",
            "sent_at",
            "approved_at",
            "rejected_at",
            "created_at",
            "items",
        ]
        read_only_fields = fields

    def get_items(self, obj):
        return QuotationItemSerializer(obj.items.all(), many=True).data


class DraftItemIn(serializers.Serializer):
    """Item aceito na criação de rascunho: exam_code ou descrição + quantidade."""

    exam_code = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    quantity = serializers.IntegerField(required=False, min_value=1)

    def validate(self, attrs):
        if not (attrs.get("exam_code") or attrs.get("description")):
            raise serializers.ValidationError("Informe exam_code ou description no item.")
        return attrs


class DraftCreateSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True)
    items = DraftItemIn(many=True)
