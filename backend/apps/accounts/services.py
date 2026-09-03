"""Serviços de autenticação (doc 11) — lockout e auditoria aplicados aqui."""
import logging

from django.contrib.auth import authenticate
from rest_framework.exceptions import APIException
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.audit.models import record as audit_record

logger = logging.getLogger(__name__)


class AccountLocked(APIException):
    """Conta temporariamente bloqueada (423)."""

    status_code = 423
    default_detail = "Conta temporariamente bloqueada por excesso de tentativas."
    default_code = "account_locked"


class InvalidCredentials(APIException):
    """Credenciais inválidas (401) — resposta genérica de segurança."""

    status_code = 401
    default_detail = "E-mail ou senha inválidos."
    default_code = "invalid_credentials"


def _client_info(request):
    ip = request.META.get("REMOTE_ADDR")
    ua = request.META.get("HTTP_USER_AGENT", "")
    return ip, ua


def _audit(request, action, user=None, entity_id=None, metadata=None):
    ip, ua = _client_info(request)
    audit_record(
        action=action,
        entity_type="accounts.User",
        entity_id=entity_id if entity_id is not None else (user.pk if user else None),
        user=user,
        ip=ip,
        user_agent=ua,
        metadata=metadata or {},
    )


def login_user(email, password, request):
    """Autentica por e-mail/senha aplicando lockout e auditoria (doc 11 §1-2).

    Retorna (dict tokens, User) ou levanta AuthenticationFailed/AccountLocked.
    """
    email = (email or "").strip().lower()
    user = User.objects.filter(email__iexact=email).first()

    if user is not None and user.is_locked():
        _audit(
            request,
            "auth.login_blocked",
            user=user,
            metadata={"remaining_seconds": user.remaining_lock_seconds()},
        )
        raise AccountLocked()

    authenticated = authenticate(request=request, username=email, password=password or "")
    if authenticated is None:
        if user is not None and user.is_active:
            blocked_now = user.register_failed_login()
            _audit(
                request,
                "auth.login_failed",
                user=user,
                metadata={"attempts": user.failed_login_attempts, "blocked": blocked_now},
            )
            if blocked_now:
                _audit(request, "auth.account_locked", user=user)
                raise AccountLocked()
        else:
            # e-mail inexistente ou usuário inativo: resposta genérica
            _audit(request, "auth.login_failed", metadata={"email": email})
        raise InvalidCredentials()

    user.reset_failed_login()
    _audit(request, "auth.login", user=authenticated)

    refresh = RefreshToken.for_user(authenticated)
    refresh["role"] = authenticated.role_code or ""
    tokens = {"access": str(refresh.access_token), "refresh": str(refresh)}
    return tokens, authenticated


def logout_user(refresh_token_raw, request, user=None):
    """Blacklist do refresh token (doc 11 §3). Idempotente."""
    from rest_framework_simplejwt.exceptions import TokenError
    from rest_framework_simplejwt.tokens import RefreshToken

    try:
        token = RefreshToken(refresh_token_raw)
        token.blacklist()
        _audit(request, "auth.logout", user=user or token.get("user_id"))
    except TokenError:
        logger.warning("Logout com token de refresh inválido (idempotente).")
