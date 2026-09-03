"""Payment (doc 06 §2-3) — financeiro da solicitação (doc 10).

Estados (doc 10 §2): PENDING, LINK_CREATED, AUTHORIZED, CONFIRMED, FAILED,
REFUNDED, CANCELED. Regra crítica: a CONFIRMAÇÃO não altera o status da
solicitação — pagamento nunca bloqueia a realização (ADR-008 / CT-INT-005).
"""
import secrets
from datetime import date

from django.conf import settings
from django.db import models


def _code():
    today = date.today().strftime("%Y%m%d")
    return f"PY-{today}-{secrets.token_hex(3).upper()}"


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pendente"
    LINK_CREATED = "LINK_CREATED", "Link criado"
    AUTHORIZED = "AUTHORIZED", "Autorizado"
    CONFIRMED = "CONFIRMED", "Confirmado"
    FAILED = "FAILED", "Falhou"
    REFUNDED = "REFUNDED", "Estornado"
    CANCELED = "CANCELED", "Cancelado"


class PaymentMethod(models.TextChoices):
    LINK = "link", "Link de pagamento"
    PRESENTIAL = "presencial", "Presencial na coleta"


class Payment(models.Model):
    code = models.CharField(max_length=20, unique=True, default=_code, editable=False)
    request = models.ForeignKey(
        "requests.CollectionRequest",
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="solicitação",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="valor")
    method = models.CharField(max_length=16, choices=PaymentMethod.choices)
    status = models.CharField(
        max_length=16, choices=PaymentStatus.choices, default=PaymentStatus.PENDING,
        db_index=True,
        verbose_name="status",
    )
    gateway_provider = models.CharField(max_length=32, default="fake", verbose_name="provedor")
    external_reference = models.CharField(
        max_length=64, null=True, blank=True, unique=True, verbose_name="referência externa"
    )
    payment_url = models.URLField(blank=True, verbose_name="URL de pagamento")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="pago em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_payments",
        verbose_name="criado por",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "pagamento"
        verbose_name_plural = "pagamentos"

    def __str__(self) -> str:
        return f"{self.code} ({self.status})"
