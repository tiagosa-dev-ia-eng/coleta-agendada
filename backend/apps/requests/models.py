"""CollectionRequest, MedicalOrder e RequestStatusHistory (doc 06 §2-3, doc 05 §5).

Storage de anexos: LOCAL (MEDIA_ROOT/media) por decisão G-07 (03/09/2026).
Evolução futura: trocar para object storage S3-compatible (django-storages) em
produção — basta trocar o DEFAULT_FILE_STORAGE e manter upload_to relativo.
"""
import secrets
from datetime import date

from django.conf import settings
from django.db import models

from apps.requests.statuses import CollectionMode, DesiredPeriod, RequestStatus


def _result_token():
    import secrets

    return secrets.token_urlsafe(20)


def _protocol():
    today = date.today().strftime("%Y%m%d")
    return f"CA-{today}-{secrets.token_hex(3).upper()}"


def medical_order_upload_path(instance, filename):
    return f"medical_orders/{instance.request_id}/{filename}"


class CollectionRequest(models.Model):
    """Solicitação de coleta (doc 06) — cria o processo do paciente."""

    protocol = models.CharField(
        max_length=20, unique=True, default=_protocol, editable=False, verbose_name="protocolo"
    )
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="requests",
        verbose_name="paciente",
    )
    laboratory = models.ForeignKey(
        "organizations.Laboratory",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="requests",
        verbose_name="laboratório responsável",
    )
    desired_date = models.DateField(null=True, blank=True, verbose_name="data desejada")
    desired_period = models.CharField(
        max_length=16, choices=DesiredPeriod.choices, blank=True, verbose_name="período desejado"
    )
    collection_mode = models.CharField(
        max_length=16,
        choices=CollectionMode.choices,
        default=CollectionMode.PHARMACY,
        verbose_name="modalidade",
    )
    preferred_location = models.CharField(
        max_length=255, blank=True, verbose_name="local preferido"
    )
    status = models.CharField(
        max_length=32,
        choices=RequestStatus.choices,
        default=RequestStatus.REQUESTED,
        db_index=True,
        verbose_name="status",
    )
    notes = models.TextField(blank=True, verbose_name="observações")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "solicitação de coleta"
        verbose_name_plural = "solicitações de coleta"

    def __str__(self) -> str:
        return f"{self.protocol} ({self.status})"


class MedicalOrder(models.Model):
    """Pedido médico anexado (RF-003). Arquivo físico em storage local (G-07)."""

    request = models.ForeignKey(
        CollectionRequest,
        on_delete=models.CASCADE,
        related_name="medical_orders",
        verbose_name="solicitação",
    )
    file = models.FileField(
        upload_to=medical_order_upload_path, verbose_name="arquivo"
    )
    mime_type = models.CharField(max_length=100, blank=True, verbose_name="tipo MIME")
    original_name = models.CharField(max_length=255, blank=True, verbose_name="nome original")
    size = models.PositiveIntegerField(default=0, verbose_name="tamanho (bytes)")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_medical_orders",
        verbose_name="enviado por",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "pedido médico"
        verbose_name_plural = "pedidos médicos"

    def __str__(self) -> str:
        return f"{self.original_name} ({self.request.protocol})"


class RequestStatusHistory(models.Model):
    """Trilha de transições (doc 05 §5): anterior, novo, responsável, origem, motivo."""

    request = models.ForeignKey(
        CollectionRequest,
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name="solicitação",
    )
    from_status = models.CharField(
        max_length=32, choices=RequestStatus.choices, verbose_name="estado anterior"
    )
    to_status = models.CharField(
        max_length=32, choices=RequestStatus.choices, verbose_name="estado novo"
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="request_status_changes",
        verbose_name="responsável",
    )
    origin = models.CharField(
        max_length=32, default="system", verbose_name="origem"
    )  # user | system | whatsapp | ia
    reason = models.CharField(max_length=255, blank=True, verbose_name="motivo")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="metadados")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "histórico de status"
        verbose_name_plural = "históricos de status"

    def __str__(self) -> str:
        return f"{self.request.protocol}: {self.from_status} -> {self.to_status}"


class ExamResult(models.Model):
    """Resultado de exame (D-06/D-07): URL externa e página pública de resultado.

    O laboratório registra a URL com o resultado (sistema externo) e publica;
    a publicação gera token de acesso para a PÁGINA pública do resultado.
    """

    request = models.ForeignKey(
        CollectionRequest,
        on_delete=models.CASCADE,
        related_name="exam_results",
        verbose_name="solicitação",
    )
    token = models.CharField(
        max_length=48, unique=True, default=_result_token, editable=False, verbose_name="token"
    )
    result_url = models.URLField(
        blank=True, verbose_name="URL externa do resultado"
    )
    note = models.TextField(blank=True, verbose_name="observação do resultado")
    published = models.BooleanField(default=False, verbose_name="publicado")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="publicado em")
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="published_exam_results",
        verbose_name="publicado por",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_exam_results",
        verbose_name="criado por",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "resultado de exame"
        verbose_name_plural = "resultados de exames"

    def __str__(self) -> str:
        state = "publicado" if self.published else "rascunho"
        return f"Resultado {self.request.protocol} ({state})"

    def page_url(self):
        return f"/api/v1/results/{self.token}/page"
