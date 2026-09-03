"""Technician (doc 06 §2-3) — executores de coleta da rede de um laboratório."""
from django.conf import settings
from django.db import models

STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
STATUS_CHOICES = [
    (STATUS_ACTIVE, "Ativo"),
    (STATUS_INACTIVE, "Inativo"),
]


class Technician(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="technician_profile",
        verbose_name="usuário",
    )
    laboratory = models.ForeignKey(
        "organizations.Laboratory",
        on_delete=models.CASCADE,
        related_name="technicians",
        verbose_name="laboratório",
    )
    reseller = models.ForeignKey(
        "organizations.Reseller",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="technicians",
        verbose_name="revendedor",
    )
    professional_registration = models.CharField(
        max_length=30, blank=True, verbose_name="registro profissional"
    )
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE, verbose_name="status"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "técnico"
        verbose_name_plural = "técnicos"

    def __str__(self) -> str:
        return self.user.email
