"""CommissionService — cálculo e gatilhos (doc 10, ADR-010, decisão G-03)."""
import logging
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from django.utils import timezone

from apps.audit.models import record as audit_record
from apps.commissions.models import (
    BeneficiaryType,
    CalculationType,
    Commission,
    CommissionRule,
    CommissionStatus,
    CommissionTrigger,
)

logger = logging.getLogger(__name__)

MONEY = Decimal("0.01")


def _money(value) -> Decimal:
    return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def _beneficiaries(request_obj):
    """Beneficiários potenciais da solicitação (via agendamento e rede)."""
    from apps.organizations.models import Pharmacy
    from apps.technicians.models import Technician

    result = []
    appt = getattr(request_obj, "appointment", None)
    if appt is None:
        return result
    if appt.pharmacy_id:
        result.append((BeneficiaryType.PHARMACY, appt.pharmacy_id))
        res = (
            Pharmacy.objects.filter(pk=appt.pharmacy_id)
            .values_list("reseller_id", flat=True)
            .first()
        )
        if res:
            result.append((BeneficiaryType.RESELLER, res))
    if appt.technician_id:
        result.append((BeneficiaryType.TECHNICIAN, appt.technician_id))
        res = (
            Technician.objects.filter(pk=appt.technician_id)
            .values_list("reseller_id", flat=True)
            .first()
        )
        if res:
            result.append((BeneficiaryType.RESELLER, res))
    return result


class CommissionService:
    """Serviço de comissões — lançamentos imutáveis (ADR-010)."""

    @staticmethod
    def generate_for_trigger(request_obj, trigger, *, lab=None, payment=None):
        """Gera lançamentos para o gatilho (FIXED/coleta, PERCENTAGE/pagamento)."""
        from django.db.models import Q

        today = date.today()
        lab = lab or request_obj.laboratory
        if lab is None:
            return []
        created = []
        for btype, bid in _beneficiaries(request_obj):
            rules = CommissionRule.objects.filter(
                laboratory=lab,
                beneficiary_type=btype,
                trigger=trigger,
                active=True,
            ).filter(Q(valid_from__isnull=True) | Q(valid_from__lte=today)).filter(
                Q(valid_until__isnull=True) | Q(valid_until__gte=today)
            )
            rules = [r for r in rules if r.beneficiary_id in (None, bid)]
            for rule in rules:
                if rule.calculation_type == CalculationType.PERCENTAGE:
                    # G-03: percentual só dispara na confirmação do pagamento
                    if trigger != CommissionTrigger.PAYMENT_CONFIRMED:
                        continue
                else:
                    # G-03: fixo só dispara na conclusão da coleta
                    if trigger != CommissionTrigger.COLLECTION_COMPLETED:
                        continue
                ledger = CommissionService._create_ledger(
                    request_obj, btype, bid, rule, payment=payment, lab=lab
                )
                if ledger is not None:
                    created.append(ledger)
        return created

    def _create_ledger(request_obj, btype, bid, rule, *, payment=None, lab=None):
        if rule.calculation_type == CalculationType.PERCENTAGE:
            if payment is None or payment.amount is None:
                return None
            base = payment.amount
            amount = _money(base * rule.value / Decimal("100"))
        else:
            base = None
            amount = rule.value
        existing = Commission.objects.filter(
            request=request_obj,
            beneficiary_type=btype,
            beneficiary_id=bid,
            rule=rule,
        ).first()
        if existing:
            return None  # idempotência
        ledger = Commission.objects.create(
            request=request_obj,
            beneficiary_type=btype,
            beneficiary_id=bid,
            rule=rule,
            calculation_type=rule.calculation_type,
            rule_value=rule.value,
            trigger=rule.trigger,
            base_amount=base,
            amount=amount,
            payment=payment,
        )
        audit_record(
            action="commission.generated",
            entity_type="commissions.Commission",
            entity_id=ledger.pk,
            metadata={
                "protocol": request_obj.protocol,
                "beneficiary": f"{btype}:{bid}",
                "amount": str(amount),
                "trigger": trigger_of(rule),
            },
        )
        return ledger

    @staticmethod
    def mark_paid(ledger, *, user, http_request=None):
        """Financeiro marca a comissão como paga (doc 10)."""
        if ledger.status in (CommissionStatus.PAID, CommissionStatus.REVERSED):
            return ledger
        ledger.status = CommissionStatus.PAID
        ledger.paid_at = timezone.now()
        ledger.save(update_fields=["status", "paid_at"])
        _audit_http(http_request, user, "commission.paid", ledger)
        return ledger

    @staticmethod
    def reverse(ledger, *, user, reason="", http_request=None):
        """Estorno explícito (doc 10 §7) — lançamento nunca é apagado."""
        if ledger.status == CommissionStatus.REVERSED:
            return ledger
        if ledger.status == CommissionStatus.PAID:
            return ledger  # paga -> baixa financeira; estorno deve ser tratado à parte
        ledger.status = CommissionStatus.REVERSED
        ledger.reversed_at = timezone.now()
        ledger.reversed_reason = reason
        ledger.save(update_fields=["status", "reversed_at", "reversed_reason"])
        _audit_http(http_request, user, "commission.reversed", ledger, {"reason": reason})
        return ledger


def trigger_of(rule):
    return rule.trigger


def _audit_http(http_request, user, action, ledger, metadata=None):
    audit_record(
        action=action,
        entity_type="commissions.Commission",
        entity_id=ledger.pk,
        user=user,
        ip=http_request.META.get("REMOTE_ADDR") if http_request else None,
        user_agent=http_request.META.get("HTTP_USER_AGENT", "") if http_request else "",
        metadata=metadata or {},
    )


def trigger_fixed_on_completion(request_obj):
    """G-03: regras FIXED geram na conclusão da coleta (não pode quebrar a coleta)."""
    try:
        CommissionService.generate_for_trigger(
            request_obj, CommissionTrigger.COLLECTION_COMPLETED
        )
    except Exception:  # noqa: BLE001 — comissão não pode bloquear a coleta (ADR-008/espírito)
        logger.exception("Falha ao gerar comissões fixas da coleta %s", request_obj.protocol)


def trigger_percentage_on_payment(request_obj, payment):
    """G-03: regras PERCENTAGE geram na confirmação do pagamento (base = valor pago)."""
    try:
        CommissionService.generate_for_trigger(
            request_obj, CommissionTrigger.PAYMENT_CONFIRMED, payment=payment
        )
    except Exception:  # noqa: BLE001
        logger.exception("Falha ao gerar comissões percentuais do pagamento %s", payment.code)
