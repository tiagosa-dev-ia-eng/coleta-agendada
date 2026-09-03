from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts import rbac
from apps.accounts.models import Role
from apps.accounts.services import login_user

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        request = self.context.get("request")
        tokens, user = login_user(attrs["email"], attrs["password"], request)
        attrs["tokens"] = tokens
        attrs["user"] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


def role_info(user):
    return (
        {"code": user.role.code, "name": user.role.name}
        if user.role is not None
        else None
    )


class UserReadSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    name = serializers.CharField(source="full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "name",
            "first_name",
            "last_name",
            "phone",
            "document",
            "role",
            "permissions",
            "is_active",
            "last_login",
            "date_joined",
        ]
        read_only_fields = fields

    def get_role(self, obj):
        return role_info(obj)

    def get_permissions(self, obj):
        return sorted(rbac.ROLE_PERMISSIONS.get(obj.role_code, ()))


class UserCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    document = serializers.CharField(required=False, allow_blank=True)
    role_code = serializers.ChoiceField(choices=rbac.role_codes())
    is_active = serializers.BooleanField(default=True)

    def validate_email(self, value):
        email = (value or "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Já existe um usuário com este e-mail.")
        return email

    def create(self, validated_data):
        role_code = validated_data.pop("role_code")
        password = validated_data.pop("password")
        role = Role.objects.get(code=role_code)
        user = User(role=role, **validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.Serializer):
    """Atualização parcial por gestor (user.manage)."""

    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    document = serializers.CharField(required=False, allow_blank=True)
    role_code = serializers.ChoiceField(choices=rbac.role_codes(), required=False)
    is_active = serializers.BooleanField(required=False)
    password = serializers.CharField(min_length=8, write_only=True, required=False)

    def update(self, instance, validated_data):
        role_code = validated_data.pop("role_code", None)
        password = validated_data.pop("password", None)
        if role_code is not None:
            instance.role = Role.objects.get(code=role_code)
        if password:
            instance.set_password(password)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance
