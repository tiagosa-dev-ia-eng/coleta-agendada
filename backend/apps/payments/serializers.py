from decimal import Decimal

from rest_framework import serializers

from apps.payments.models import Payment


class AmountSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )


class PaymentReadSerializer(serializers.ModelSerializer):
    request_protocol = serializers.CharField(source="request.protocol", read_only=True)
    method_display = serializers.CharField(source="get_method_display", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "code",
            "request_id",
            "request_protocol",
            "amount",
            "method",
            "method_display",
            "status",
            "gateway_provider",
            "external_reference",
            "payment_url",
            "paid_at",
            "created_at",
        ]
        read_only_fields = fields
