"""Laboratory, Reseller e Pharmacy (doc 06 §2-3).

Um perfil organizacional vincula um usuário (accounts.User) à organização a que
pertence — base do escopo de visão do doc 04 §3-4 (menor privilégio).
"""
from django.conf import settings
from django.db import models

STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
STATUS_CHOICES = [
    (STATUS_ACTIVE, "Ativo"),
    (STATUS_INACTIVE, "Inativo"),
]


class Laboratory(models.Model):
    """Laboratório — administra a operação e a rede (doc 04)."""

    name = models.CharField(max_length=160, verbose_name="nome")
    document = models.CharField(
        max_length=20, blank=True, null=True, unique=True, verbose_name="CNPJ"
    )
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_laboratory",
        verbose_name="usuário administrador",
    )
    # Localização da unidade — o laboratório também é um local de coleta (D-01:
    # ponto de coleta = farmácia OU laboratório, decisão do usuário 04/09/2026).
    address = models.CharField(max_length=255, blank=True, verbose_name="endereço")
    city = models.CharField(max_length=80, blank=True, verbose_name="cidade")
    state = models.CharField(max_length=2, blank=True, verbose_name="UF")
    zip_code = models.CharField(max_length=10, blank=True, verbose_name="CEP")
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="latitude",
        help_text="Coordenada para cálculo de proximidade (D-01).",
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="longitude",
        help_text="Coordenada para cálculo de proximidade (D-01).",
    )
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE, verbose_name="status"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "laboratório"
        verbose_name_plural = "laboratórios"

    def __str__(self) -> str:
        return self.name


class Reseller(models.Model):
    """Revendedor — indica farmácias/técnicos da rede de um laboratório."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reseller_profile",
        verbose_name="usuário",
    )
    laboratory = models.ForeignKey(
        Laboratory,
        on_delete=models.CASCADE,
        related_name="resellers",
        verbose_name="laboratório",
    )
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE, verbose_name="status"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "revendedor"
        verbose_name_plural = "revendedores"

    def __str__(self) -> str:
        return f"{self.user.email} ({self.laboratory.name})"


class Pharmacy(models.Model):
    """Farmácia/ponto de coleta (doc 04) vinculada a laboratório e revendedor."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pharmacy_profile",
        verbose_name="usuário",
    )
    laboratory = models.ForeignKey(
        Laboratory, on_delete=models.CASCADE, related_name="pharmacies", verbose_name="laboratório"
    )
    reseller = models.ForeignKey(
        Reseller,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pharmacies",
        verbose_name="revendedor",
    )
    name = models.CharField(max_length=160, verbose_name="nome")
    document = models.CharField(max_length=20, blank=True, verbose_name="CNPJ")
    address = models.CharField(max_length=255, blank=True, verbose_name="endereço")
    city = models.CharField(max_length=80, blank=True, verbose_name="cidade")
    state = models.CharField(max_length=2, blank=True, verbose_name="UF")
    zip_code = models.CharField(max_length=10, blank=True, verbose_name="CEP")
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="latitude",
        help_text="Coordenada para cálculo de proximidade (D-01).",
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="longitude",
        help_text="Coordenada para cálculo de proximidade (D-01).",
    )
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE, verbose_name="status"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "farmácia"
        verbose_name_plural = "farmácias"

    def __str__(self) -> str:
        return self.name
