"""Exam (catálogo global) e ExamPrice (preço manual por laboratório).

Decisão G-01 (03/09/2026): catálogo de exames global + tabela de preço manual
por laboratório (doc 06 §4 pendência resolvida para o MVP).
Evolução futura: preço por região/unidade/parceiro ou integração com LIS/LIS,
mantendo a mesma interface de "preço efetivo do laboratório".
"""
from django.db import models


class Exam(models.Model):
    """Exame do catálogo (doc 06 — Exam)."""

    code = models.CharField(max_length=32, unique=True, verbose_name="código")
    name = models.CharField(max_length=160, verbose_name="nome")
    active = models.BooleanField(default=True, verbose_name="ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "exame"
        verbose_name_plural = "exames"

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class ExamPrice(models.Model):
    """Preço vigente de um exame para um laboratório (preço manual — G-01)."""

    laboratory = models.ForeignKey(
        "organizations.Laboratory",
        on_delete=models.CASCADE,
        related_name="exam_prices",
        verbose_name="laboratório",
    )
    exam = models.ForeignKey(
        Exam, on_delete=models.CASCADE, related_name="prices", verbose_name="exame"
    )
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="preço")
    active = models.BooleanField(default=True, verbose_name="ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["laboratory", "exam"], name="unique_price_per_lab_exam"
            )
        ]
        ordering = ["exam__code"]
        verbose_name = "preço de exame"
        verbose_name_plural = "preços de exames"

    def __str__(self) -> str:
        return f"{self.exam.code} @ {self.laboratory.name}: R$ {self.price}"

    def effective_for(self, laboratory, exam):
        return ExamPrice.objects.filter(laboratory=laboratory, exam=exam, active=True).first()
