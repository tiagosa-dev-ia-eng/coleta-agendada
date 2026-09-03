from rest_framework import serializers

from apps.scheduling.models import Appointment, AppointmentMode
from apps.technicians.models import Technician


class AppointmentWriteSerializer(serializers.Serializer):
    """Criação do agendamento (laboratório). Farmácia/técnico são do MESMO lab."""

    mode = serializers.ChoiceField(choices=AppointmentMode.choices)
    scheduled_at = serializers.DateTimeField()
    pharmacy_id = serializers.IntegerField(required=False, allow_null=True)
    technician_id = serializers.IntegerField(required=False, allow_null=True)
    location_label = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        from apps.organizations.models import Pharmacy

        lab = self.context["laboratory"]
        mode = attrs["mode"]
        if mode == AppointmentMode.PHARMACY:
            pharm = Pharmacy.objects.filter(
                pk=attrs.get("pharmacy_id"), laboratory=lab, status="active"
            ).first()
            if pharm is None:
                raise serializers.ValidationError("Farmácia inválida ou fora do laboratório.")
            attrs["pharmacy"] = pharm
        if mode == AppointmentMode.DOMICILIARY:
            tech = Technician.objects.filter(
                pk=attrs.get("technician_id"), laboratory=lab, status="active"
            ).first()
            if tech is None:
                raise serializers.ValidationError("Técnico inválido ou fora do laboratório.")
            attrs["technician"] = tech
        return attrs


class AppointmentReadSerializer(serializers.ModelSerializer):
    request_protocol = serializers.CharField(source="request.protocol", read_only=True)
    status = serializers.CharField(source="request.status", read_only=True)
    mode_display = serializers.CharField(source="get_mode_display", read_only=True)
    laboratory_name = serializers.CharField(source="laboratory.name", read_only=True)
    pharmacy_name = serializers.SerializerMethodField()
    technician_name = serializers.SerializerMethodField()
    patient = serializers.SerializerMethodField()
    location = serializers.CharField(source="location_label", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "code",
            "request_id",
            "request_protocol",
            "status",
            "mode",
            "mode_display",
            "scheduled_at",
            "location",
            "laboratory_name",
            "pharmacy_name",
            "technician_name",
            "patient",
            "checkin_at",
            "checkout_at",
            "completed_at",
            "created_at",
        ]
        read_only_fields = fields

    def get_pharmacy_name(self, obj):
        return obj.pharmacy.name if obj.pharmacy_id else None

    def get_technician_name(self, obj):
        if obj.technician_id is None:
            return None
        return obj.technician.user.full_name

    def get_patient(self, obj):
        p = obj.request.patient
        return {"id": p.pk, "name": p.user.full_name, "email": p.user.email}
