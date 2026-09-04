"""Quotation e QuotationItem (doc 06 §2) — rascunho ≠ orçamento final (RN-ORC-001).

Versionamento (doc 09 §4): cada versão é uma linha (v1 rascunho, v2 final
validado, v3 enviado...). A validação humana PROMOVE um rascunho em nova versão
final com validated_by/validated_at; edição após validação invalida (nova
versão exige revalidação — RN-ORC-004, PROPOSTO implementado).
"""
from django.conf import settings
from django.db import models


class QuotationType(models.TextChoices):
    DRAFT = "draft", "Rascunho"
    FINAL = "final", "Orçamento final"


class ItemSource(models.TextChoices):
    CATALOG = "catalog", "Catálogo do laboratório"
    MANUAL = "manual", "Entrada manual"
    AI = "ai", "Extraído por IA"


class Quotation(models.Model):
    request = models.ForeignKey(
        "requests.CollectionRequest",
        on_delete=models.CASCADE,
        related_name="quotations",
        verbose_name="solicitação",
    )
    version = models.PositiveSmallIntegerField(default=1, verbose_name="versão")
    quotation_type = models.CharField(
        max_length=16,
        choices=QuotationType.choices,
        default=QuotationType.DRAFT,
        verbose_name="tipo",
    )
    generated_by_ai = models.BooleanField(default=False, verbose_name="gerado por IA")
    notes = models.TextField(blank=True, verbose_name="observações")
    subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="subtotal"
    )
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="total")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_quotations",
        verbose_name="criado por",
    )
    # validação humana (RN-ORC-002/003)
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="validated_quotations",
        verbose_name="validado por",
    )
    validated_at = models.DateTimeField(null=True, blank=True, verbose_name="validado em")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="enviado em")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_quotations",
        verbose_name="aprovado por",
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="aprovado em")
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="rejected_quotations",
        verbose_name="recusado por",
    )
    rejected_at = models.DateTimeField(null=True, blank=True, verbose_name="recusado em")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["request", "version"], name="unique_quote_version_per_request"
            )
        ]
        verbose_name = "orçamento"
        verbose_name_plural = "orçamentos"

    def __str__(self) -> str:
        return f"{self.request.protocol} v{self.version} ({self.get_quotation_type_display()})"

    @property
    def is_final(self) -> bool:
        return self.quotation_type == QuotationType.FINAL

    @property
    def is_validated(self) -> bool:
        return self.validated_by_id is not None and self.validated_at is not None

    @property
    def is_sent(self) -> bool:
        return self.sent_at is not None

    @property
    def is_approved(self) -> bool:
        return self.approved_at is not None

    @property
    def is_expired(self) -> bool:
        """Orçamento final expira após QUOTATION_VALIDITY_DAYS (B-05: 15 dias)."""
        from datetime import timedelta

        from django.conf import settings
        from django.utils import timezone

        if not self.is_final or self.validated_at is None:
            return False
        days = getattr(settings, "QUOTATION_VALIDITY_DAYS", 15)
        return timezone.now() > self.validated_at + timedelta(days=days)

    @property
    def missing_price_count(self) -> int:
        return self.items.filter(unit_price__isnull=True).count()


class QuotationItem(models.Model):
    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="orçamento",
    )
    exam = models.ForeignKey(
        "catalog.Exam",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="quotation_items",
        verbose_name="exame",
    )
    description = models.CharField(max_length=255, blank=True, verbose_name="descrição")
    quantity = models.PositiveSmallIntegerField(default=1, verbose_name="quantidade")
    unit_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="preço unitário"
    )
    source = models.CharField(
        max_length=16, choices=ItemSource.choices, default=ItemSource.MANUAL, verbose_name="origem"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "item de orçamento"
        verbose_name_plural = "itens de orçamento"

    def __str__(self) -> str:
        return self.description or self.exam.name if self.exam else "item"

    @property
    def total_price(self):
        if self.unit_price is None:
            return None
        return self.quantity * self.unit_price
