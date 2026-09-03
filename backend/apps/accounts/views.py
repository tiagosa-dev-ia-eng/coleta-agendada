from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.accounts import rbac
from apps.accounts.models import User
from apps.accounts.serializers import (
    LoginSerializer,
    LogoutSerializer,
    UserCreateSerializer,
    UserReadSerializer,
    UserUpdateSerializer,
    role_info,
)
from apps.accounts.services import logout_user
from apps.audit.models import record as audit_record


class LoginRateThrottle(ScopedRateThrottle):
    scope = "login"


def permission_required(*codes):
    """Fábrica de permissão RBAC para views DRF (doc 04/16)."""

    class RequirePermission(BasePermission):
        message = "Você não possui permissão para esta ação."

        def has_permission(self, request, view):
            return any(rbac.has_permission(request.user, code) for code in codes)

    return RequirePermission


class IsOwnerOrManager(BasePermission):
    """Usuário acessa o próprio registro; gestores (user.manage) acessam todos."""

    message = "Você não possui permissão para este recurso."

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.pk == request.user.pk or rbac.has_permission(request.user, "user.manage")


def _audit_request(request, action, user=None, entity_id=None, metadata=None):
    audit_record(
        action=action,
        entity_type="accounts.User",
        entity_id=entity_id,
        user=user or (request.user if request.user.is_authenticated else None),
        ip=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        metadata=metadata or {},
    )


def _login_payload(user):
    return {
        "id": user.pk,
        "email": user.email,
        "name": user.full_name,
        "role": role_info(user),
        "permissions": sorted(rbac.ROLE_PERMISSIONS.get(user.role_code, ())),
    }


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        tokens = serializer.validated_data["tokens"]
        return Response({**tokens, "user": _login_payload(user)})


class LogoutView(APIView):
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        logout_user(serializer.validated_data["refresh"], request, user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        return Response(UserReadSerializer(request.user).data)


class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """CRUD mínimo de usuários (auditado). Somente gestores com user.manage."""

    queryset = User.objects.select_related("role").order_by("-date_joined")
    lookup_field = "pk"
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ("partial_update", "update"):
            return UserUpdateSerializer
        return UserReadSerializer

    def get_permissions(self):
        if self.action in ("list", "create", "partial_update", "update"):
            return [IsAuthenticated(), permission_required("user.manage")()]
        return [IsAuthenticated(), IsOwnerOrManager()]

    def get_serializer(self, *args, **kwargs):
        kwargs.setdefault("context", {"request": self.request})
        return super().get_serializer(*args, **kwargs)

    # --- create ---
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        _audit_request(
            self.request,
            "user.created",
            entity_id=user.pk,
            metadata={"email": user.email, "role": user.role_code},
        )
        return Response(UserReadSerializer(user).data, status=status.HTTP_201_CREATED)

    # --- partial_update (gestor) ---
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.pk == request.user.pk:
            raise PermissionDenied("Não é permitido alterar a si mesmo por este endpoint.")
        before = {
            "role": instance.role_code,
            "is_active": instance.is_active,
            "email": instance.email,
        }
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        changes = {
            k: (before[k], getattr(user, k)) for k in before if getattr(user, k) != before[k]
        }
        _audit_request(
            self.request,
            "user.updated",
            entity_id=user.pk,
            metadata={"changed": changes},
        )
        return Response(UserReadSerializer(user).data)
