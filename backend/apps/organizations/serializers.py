from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts import rbac
from apps.accounts.models import Role
from apps.audit.models import record as audit_record
from apps.organizations.models import Laboratory, Pharmacy, Reseller

User = get_user_model()


class LaboratorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Laboratory
        fields = ["id", "name", "document", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


def _create_entity_user(email, password, role_code, first_name=""):
    email = (email or "").strip().lower()
    if User.objects.filter(email__iexact=email).exists():
        raise serializers.ValidationError({"email": "Já existe um usuário com este e-mail."})
    role = Role.objects.get(code=role_code)
    user = User(email=email, first_name=first_name or email.split("@")[0], role=role)
    user.set_password(password)
    user.save()
    return user


class _EntityBaseSerializer(serializers.ModelSerializer):
    """Cria usuário + perfil organizacional juntos, vinculando ao escopo da view.

    O laboratório/revendedor são passados pelo contexto (nunca aceitos do
    cliente) — garante o escopo do doc 04 §3-4 no backend.
    """

    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    user_id = serializers.IntegerField(read_only=True)
    email_read = serializers.EmailField(source="user.email", read_only=True)

    def create(self, validated_data):
        email = validated_data.pop("email")
        password = validated_data.pop("password")
        first_name = validated_data.pop("first_name", "")
        user = _create_entity_user(email, password, self.role_code(), first_name)
        validated_data["user"] = user
        context = self.context
        if context.get("laboratory") is not None:
            validated_data["laboratory"] = context["laboratory"]
        if context.get("reseller") is not None and hasattr(self.Meta.model, "reseller"):
            validated_data["reseller"] = context["reseller"]
        request = context.get("request")
        entity = super().create(validated_data)
        audit_record(
            action=f"{self.entity_name()}.created",
            entity_type=self.entity_name(),
            entity_id=entity.pk,
            user=request.user if request else user,
            ip=request.META.get("REMOTE_ADDR") if request else None,
            user_agent=request.META.get("HTTP_USER_AGENT", "") if request else "",
            metadata={"email": user.email},
        )
        return entity


class PharmacyCreateSerializer(_EntityBaseSerializer):
    class Meta:
        model = Pharmacy
        fields = [
            "id",
            "name",
            "document",
            "address",
            "city",
            "state",
            "zip_code",
            "status",
            "email",
            "password",
            "first_name",
            "user_id",
            "email_read",
        ]
        read_only_fields = ["id", "user_id", "email_read"]

    def role_code(self):
        return rbac.PHARMACY

    def entity_name(self):
        return "pharmacy"


class ResellerCreateSerializer(_EntityBaseSerializer):
    class Meta:
        model = Reseller
        fields = ["id", "status", "email", "password", "first_name", "user_id", "email_read"]
        read_only_fields = ["id", "user_id", "email_read"]

    def role_code(self):
        return rbac.RESELLER

    def entity_name(self):
        return "reseller"
