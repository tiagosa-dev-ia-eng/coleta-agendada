from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    """Pagamentos (doc 03 §4, doc 10) — não bloqueiam a coleta (ADR-008)."""

    name = "apps.payments"
    verbose_name = "Pagamentos"
