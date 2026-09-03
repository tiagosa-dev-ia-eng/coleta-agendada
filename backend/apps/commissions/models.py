"""CommissionRule e Commission (doc 06 §2-3, doc 10).

ADR-010: comissão usa regra PERSISTIDA e VERSIONADA; o lançamento (Commission)
guarda cópia da regra (tipo, valor) e a base de cálculo — imutável após a
geração (sem recálculo silencioso). Gatilho (G-03, decidido): PERCENTAGE dispara
na confirmação do pagamento; FIXED dispara na conclusão da coleta.
"""
from django.conf import settings
from django.db import models


class CalculationType(models.TextChoices):
    PERCENTAGE = "PERCENTAGE", "Percentual"
    FIXED = "FIXED", "Valor fixo"


class CommissionTrigger(models.TextChoices):
    PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED", "Confirmação do pagamento"
    COLLECTION_COMPLETED = "COLLECTION_COMPLETED", "Coleta concluída"


class BeneficiaryType(models.TextChoices):
    PHARMACY = "pharmacy", "Farmácia"
    TECHNICIAN = "technician", "Técnico"
    RESELLER = "reseller", "Revendedor"


class CommissionStatus(models.TextChoices):
    GENERATED = "GENERATED", "Gerada"
    PAID = "PAID", "Paga"
    REVERSED = "REVERSED", "Estornada"


class CommissionRule(models.Model):
    """Regra de comissão do laboratório (doc 10 §4-7)."""

    laboratory = models.ForeignKey(
        "organizations.Laboratory",
        on_delete=models.CASCADE,
        related_name="commission_rules",
        verbose_name="laboratório",
    )
    beneficiary_type = models.CharField(max_length=16, choices=BeneficiaryType.choices)
    beneficiary_id = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="beneficiário específico (opcional)"
    )
    calculation_type = models.CharField(max_length=16, choices=CalculationType.choices)
    value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="valor")
    trigger = models.CharField(max_length=32, choices=CommissionTrigger.choices)
    valid_from = models.DateField(null=True, blank=True, verbose_name="válida de")
    valid_until = models.DateField(null=True, blank=True, verbose_name="válida até")
    active = models.BooleanField(default=True, verbose_name="ativa")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_commission_rules",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "regra de comissão"
        verbose_name_plural = "regras de comissão"

    def __str__(self) -> str:
        bt = self.get_beneficiary_type_display()
        return f"{bt} {self.calculation_type} {self.value} ({self.trigger})"


class Commission(models.Model):
    """Lançamento de comissão — imutável após gerado (guarda cópia da regra)."""

    request = models.ForeignKey(
        "requests.CollectionRequest",
        on_delete=models.CASCADE,
        related_name="commissions",
        verbose_name="solicitação",
    )
    beneficiary_type = models.CharField(max_length=16, choices=BeneficiaryType.choices)
    beneficiary_id = models.PositiveIntegerField(verbose_name="id do beneficiário")
    rule = models.ForeignKey(
        CommissionRule,
        on_delete=models.SET_NULL,
        null=True,
        related_name="ledger",
        verbose_name="regra",
    )
    # snapshot imutável da regra usada (doc 16: gravar regra usada + base)
    calculation_type = models.CharField(max_length=16, choices=CalculationType.choices)
    rule_value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="valor da regra")
    trigger = models.CharField(max_length=32, choices=CommissionTrigger.choices)
    base_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="base de cálculo"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="valor")
    status = models.CharField(
        max_length=16, choices=CommissionStatus.choices, default=CommissionStatus.GENERATED,
        db_index=True,
        verbose_name="status",
    )
    payment = models.ForeignKey(
        "payments.Payment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="commissions",
        verbose_name="pagamento de origem",
    )
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="paga em")
    reversed_at = models.DateTimeField(null=True, blank=True, verbose_name="estornada em")
    reversed_reason = models.CharField(max_length=255, blank=True, verbose_name="motivo do estorno")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["request", "beneficiary_type", "beneficiary_id", "rule"],
                name="unique_commission_per_rule_beneficiary",
            )
        ]
        verbose_name = "comissão"
        verbose_name_plural = "comissões"

    def __str__(self) -> str:
        return (
            f"{self.request.protocol} {self.beneficiary_type}:"
            f"{self.beneficiary_id} R$ {self.amount}"
        )
