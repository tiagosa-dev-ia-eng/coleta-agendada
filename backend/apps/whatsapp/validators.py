"""Validadores do canal WhatsApp (contatos D-04 e telefones do pipeline)."""
import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

_PHONE_RE = re.compile(r"\D")
_BSUID_RE = re.compile(r"@[A-Za-z0-9][A-Za-z0-9._-]*")


def normalize_phone_digits(value):
    """Remove tudo que não é dígito (E.164 sem '+')."""
    return _PHONE_RE.sub("", str(value or ""))


def validate_meta_bsuid(value):
    """Handle BSUID da Meta: começa com '@' e contém nome do usuário."""
    candidate = str(value or "").strip()
    if not candidate:
        return
    if not _BSUID_RE.fullmatch(candidate):
        raise ValidationError(
            _('BSUID inválido — padrão Meta "@nome.usuario" (ex.: "@drogasil.sp").')
        )
