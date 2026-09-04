"""Patient (doc 06 §2-3) — titular das solicitações de coleta."""
from django.conf import settings
from django.db import models

STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
STATUS_CHOICES = [
    (STATUS_ACTIVE, "Ativo"),
    (STATUS_INACTIVE, "Inativo"),
]


class Patient(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_profile",
        verbose_name="usuário",
    )
    birth_date = models.DateField(null=True, blank=True, verbose_name="data de nascimento")
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE, verbose_name="status"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "paciente"
        verbose_name_plural = "pacientes"

    def __str__(self) -> str:
        return self.user.email


class PatientConsent(models.Model):
    """Registro de consentimento LGPD (B-04) — trilha de decisões do titular."""

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="consents",
        verbose_name="paciente",
    )
    purpose = models.CharField(
        max_length=120, default="dados_pessoais_servicos", verbose_name="finalidade"
    )
    granted = models.BooleanField(default=True, verbose_name="consentiu")
    ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP")
    user_agent = models.TextField(blank=True, verbose_name="user agent")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "consentimento (LGPD)"
        verbose_name_plural = "consentimentos (LGPD)"

    def __str__(self) -> str:
        state = "consentiu" if self.granted else "retirou consentimento"
        return f"{self.patient} — {state} ({self.purpose})"
