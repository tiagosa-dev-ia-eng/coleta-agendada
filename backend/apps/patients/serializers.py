from rest_framework import serializers

from apps.accounts import rbac
from apps.audit.models import record as audit_record
from apps.patients.models import Patient


class PatientCreateSerializer(serializers.ModelSerializer):
    """Cadastro de paciente (uso administrativo; autosserviço = PENDENTE)."""

    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
    user_id = serializers.IntegerField(read_only=True)
    email_read = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Patient
        fields = [
            "id",
            "birth_date",
            "status",
            "email",
            "password",
            "first_name",
            "user_id",
            "email_read",
        ]
        read_only_fields = ["id", "user_id", "email_read"]

    def create(self, validated_data):
        from apps.organizations.serializers import _create_entity_user

        email = validated_data.pop("email")
        password = validated_data.pop("password")
        first_name = validated_data.pop("first_name", "")
        user = _create_entity_user(email, password, rbac.PATIENT, first_name)
        validated_data["user"] = user
        request = self.context.get("request")
        patient = super().create(validated_data)
        audit_record(
            action="patient.created",
            entity_type="patient",
            entity_id=patient.pk,
            user=request.user if request else user,
            ip=request.META.get("REMOTE_ADDR") if request else None,
            user_agent=request.META.get("HTTP_USER_AGENT", "") if request else "",
            metadata={"email": user.email},
        )
        return patient
