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
