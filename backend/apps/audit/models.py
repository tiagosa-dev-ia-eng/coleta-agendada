"""AuditLog — trilha de auditoria (doc 06 §2 e doc 11 §5).

Registra ações sensíveis do sistema: login, mudanças de permissão, transições
críticas de estado, orçamentos, pagamentos, comissões etc. (preenchimento a
partir do M1, quando os serviços de domínio forem criados.)
"""
from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        verbose_name="usuário",
    )
    action = models.CharField(max_length=64, verbose_name="ação", db_index=True)
    entity_type = models.CharField(max_length=64, verbose_name="tipo de entidade")
    entity_id = models.CharField(
        max_length=64, null=True, blank=True, verbose_name="id da entidade"
    )
    ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP")
    user_agent = models.TextField(blank=True, verbose_name="user agent")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="metadados")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="criado em")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "log de auditoria"
        verbose_name_plural = "logs de auditoria"

    def __str__(self) -> str:
        ts = self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return f"{self.action} {self.entity_type}:{self.entity_id or '-'} @ {ts}"


def record(
    *,
    action: str,
    entity_type: str,
    entity_id=None,
    user=None,
    ip=None,
    user_agent="",
    metadata=None,
) -> AuditLog:
    """Cria um registro de auditoria de forma explícita (serviço mínimo do app audit)."""
    return AuditLog.objects.create(
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        user=user,
        ip=ip,
        user_agent=user_agent,
        metadata=metadata or {},
    )
