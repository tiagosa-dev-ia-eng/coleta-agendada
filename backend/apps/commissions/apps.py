from django.apps import AppConfig


class CommissionsConfig(AppConfig):
    """Comissões (doc 03 §4, doc 10) — regra versionada + lançamento imutável (ADR-010)."""

    name = "apps.commissions"
    verbose_name = "Comissões"
