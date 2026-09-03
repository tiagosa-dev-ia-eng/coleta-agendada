from rest_framework import serializers

from apps.commissions.models import Commission, CommissionRule


class CommissionRuleSerializer(serializers.ModelSerializer):
    beneficiary_type_display = serializers.CharField(
        source="get_beneficiary_type_display", read_only=True
    )
    calculation_type_display = serializers.CharField(
        source="get_calculation_type_display", read_only=True
    )
    trigger_display = serializers.CharField(source="get_trigger_display", read_only=True)

    class Meta:
        model = CommissionRule
        fields = [
            "id",
            "beneficiary_type",
            "beneficiary_type_display",
            "beneficiary_id",
            "calculation_type",
            "calculation_type_display",
            "value",
            "trigger",
            "trigger_display",
            "valid_from",
            "valid_until",
            "active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class CommissionReadSerializer(serializers.ModelSerializer):
    request_protocol = serializers.CharField(source="request.protocol", read_only=True)
    beneficiary_name = serializers.SerializerMethodField()
    calculation_type_display = serializers.CharField(
        source="get_calculation_type_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Commission
        fields = [
            "id",
            "request_id",
            "request_protocol",
            "beneficiary_type",
            "beneficiary_id",
            "beneficiary_name",
            "calculation_type",
            "calculation_type_display",
            "rule_value",
            "base_amount",
            "amount",
            "status",
            "status_display",
            "paid_at",
            "reversed_at",
            "reversed_reason",
            "created_at",
        ]
        read_only_fields = fields

    def get_beneficiary_name(self, obj):
        from apps.organizations.models import Pharmacy, Reseller
        from apps.technicians.models import Technician

        if obj.beneficiary_type == "pharmacy":
            p = Pharmacy.objects.filter(pk=obj.beneficiary_id).first()
            return p.name if p else None
        if obj.beneficiary_type == "technician":
            p = Technician.objects.filter(pk=obj.beneficiary_id).first()
            return p.user.full_name if p else None
        if obj.beneficiary_type == "reseller":
            p = Reseller.objects.filter(pk=obj.beneficiary_id).first()
            return p.user.full_name if p else None
        return None
