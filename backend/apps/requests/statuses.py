"""Máquina de estados da solicitação (doc 05 §1-2) — fonte única das transições.

Regras (AGENTS.md §5 / doc 05):
- estados só mudam através de serviços de domínio (RequestStateService);
- toda transição gera RequestStatusHistory + auditoria;
- pagamento não bloqueia a conclusão da coleta (validado no M5+).
"""
from django.db import models


class RequestStatus(models.TextChoices):
    REQUESTED = "REQUESTED", "Solicitado"
    QUOTE_DRAFT = "QUOTE_DRAFT", "Rascunho do orçamento"
    WAITING_HUMAN_VALIDATION = "WAITING_HUMAN_VALIDATION", "Validação humana"
    QUOTE_SENT = "QUOTE_SENT", "Orçamento final enviado"
    APPROVED = "APPROVED", "Aprovado"
    SCHEDULED = "SCHEDULED", "Agendado"
    IN_PROGRESS = "IN_PROGRESS", "Em realização"
    COMPLETED = "COMPLETED", "Realizado"
    PAYMENT_PENDING = "PAYMENT_PENDING", "Pagamento pendente"
    PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED", "Pagamento confirmado"
    COMMISSION_PENDING = "COMMISSION_PENDING", "Comissão pendente"
    COMMISSION_GENERATED = "COMMISSION_GENERATED", "Comissão gerada"
    CANCELED = "CANCELED", "Cancelado"


class CollectionMode(models.TextChoices):
    PHARMACY = "pharmacy", "Farmácia / ponto de coleta"
    DOMICILIARY = "domiciliary", "Coleta domiciliar"
    LABORATORY = "laboratory", "Laboratório / unidade"


class DesiredPeriod(models.TextChoices):
    MORNING = "morning", "Manhã"
    AFTERNOON = "afternoon", "Tarde"
    EVENING = "evening", "Noite"


# Transições válidas (doc 05). Estados financeiros/comissão entram no M5+.
TRANSITIONS = {
    RequestStatus.REQUESTED: {
        RequestStatus.QUOTE_DRAFT,
        RequestStatus.CANCELED,
    },
    RequestStatus.QUOTE_DRAFT: {
        RequestStatus.WAITING_HUMAN_VALIDATION,
        RequestStatus.CANCELED,
    },
    RequestStatus.WAITING_HUMAN_VALIDATION: {
        RequestStatus.QUOTE_SENT,
        RequestStatus.QUOTE_DRAFT,  # revisão RN-ORC-004 (nova versão)
        RequestStatus.CANCELED,
    },
    RequestStatus.QUOTE_SENT: {
        RequestStatus.APPROVED,
        RequestStatus.QUOTE_DRAFT,  # revisão RN-ORC-004 (nova versão)
        RequestStatus.CANCELED,
    },
    RequestStatus.APPROVED: {RequestStatus.SCHEDULED},
    RequestStatus.SCHEDULED: {RequestStatus.IN_PROGRESS},
    RequestStatus.IN_PROGRESS: {RequestStatus.COMPLETED},
    # pagamento/comissão (M6/M7): gatilhos e regras específicos serão adicionados
    # sem violar "pagamento não bloqueia a coleta" (CT-INT-005).
    RequestStatus.COMPLETED: set(),
    RequestStatus.PAYMENT_PENDING: {RequestStatus.PAYMENT_CONFIRMED},
    RequestStatus.PAYMENT_CONFIRMED: {RequestStatus.COMMISSION_PENDING},
    RequestStatus.COMMISSION_PENDING: {RequestStatus.COMMISSION_GENERATED},
    RequestStatus.COMMISSION_GENERATED: set(),
    RequestStatus.CANCELED: set(),
}


def is_terminal(status) -> bool:
    return not TRANSITIONS.get(status)


def valid_from(status) -> set:
    return set(TRANSITIONS.get(status, ()))
