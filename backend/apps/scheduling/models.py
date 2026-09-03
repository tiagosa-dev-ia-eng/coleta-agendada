"""Appointment (doc 06 §2-3) — agendamento da coleta aprovada.

Modalidades (RF-010): farmácia/ponto de coleta, domiciliar, laboratório.
Regra crítica (ADR-008 / CT-INT-005): a CONCLUSÃO da coleta não depende de
pagamento — o domínio de pagamento (M6) não bloqueia COMPLETED.
"""
import secrets
from datetime import date

from django.conf import settings
from django.db import models


def _code():
    today = date.today().strftime("%Y%m%d")
    return f"AP-{today}-{secrets.token_hex(3).upper()}"


class AppointmentMode(models.TextChoices):
    PHARMACY = "pharmacy", "Farmácia / ponto de coleta"
    DOMICILIARY = "domiciliary", "Coleta domiciliar"
    LABORATORY = "laboratory", "Laboratório / unidade"


class Appointment(models.Model):
    request = models.OneToOneField(
        "requests.CollectionRequest",
        on_delete=models.CASCADE,
        related_name="appointment",
        verbose_name="solicitação",
    )
    code = models.CharField(max_length=20, unique=True, default=_code, editable=False)
    mode = models.CharField(max_length=16, choices=AppointmentMode.choices)
    laboratory = models.ForeignKey(
        "organizations.Laboratory",
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name="laboratório",
    )
    pharmacy = models.ForeignKey(
        "organizations.Pharmacy",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="appointments",
        verbose_name="farmácia / ponto",
    )
    technician = models.ForeignKey(
        "technicians.Technician",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="appointments",
        verbose_name="técnico",
    )
    scheduled_at = models.DateTimeField(verbose_name="data e hora agendadas")
    location_label = models.CharField(max_length=255, blank=True, verbose_name="local")
    checkin_at = models.DateTimeField(null=True, blank=True, verbose_name="check-in em")
    checkout_at = models.DateTimeField(null=True, blank=True, verbose_name="check-out em")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="concluída em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_appointments",
        verbose_name="criado por",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scheduled_at"]
        verbose_name = "agendamento"
        verbose_name_plural = "agendamentos"

    def __str__(self) -> str:
        return f"{self.code} ({self.request.protocol})"

    @property
    def status(self):
        return self.request.status
