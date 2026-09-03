"""Resolução de escopo organizacional (doc 04 §3-4).

Centraliza "a qual laboratório/revendedor este usuário pertence", evitando
espalhar regras de escopo pelas views (regra 5 do AGENTS.md).
"""
from django.db.models import Model

from apps.accounts import rbac


def role_of(user):
    return user.role_code if user.is_authenticated else None


def laboratory_of(user) -> Model | None:
    """Laboratório do usuário conforme o papel (doc 04: cada perfil vê sua rede)."""
    role = role_of(user)
    if role is None:
        return None
    if role == rbac.LABORATORY:
        return getattr(user, "owned_laboratory", None)
    profile = getattr(user, "reseller_profile", None) or getattr(user, "pharmacy_profile", None)
    if profile is None and role == rbac.TECHNICIAN:
        profile = getattr(user, "technician_profile", None)
    return profile.laboratory if profile is not None else None


def reseller_of(user) -> Model | None:
    """Revendedor do usuário (para farmácia/técnico indicados por revendedor)."""
    role = role_of(user)
    if role == rbac.RESELLER:
        return getattr(user, "reseller_profile", None)
    profile = getattr(user, "pharmacy_profile", None)
    if profile is None and role == rbac.TECHNICIAN:
        profile = getattr(user, "technician_profile", None)
    return profile.reseller if profile is not None else None


def is_laboratory_admin(user) -> bool:
    """Usuário do papel laboratório já vinculado a uma organização."""
    return (
        role_of(user) == rbac.LABORATORY
        and getattr(user, "owned_laboratory", None) is not None
    )
