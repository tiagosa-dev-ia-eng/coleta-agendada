"""WhatsAppConversation e WhatsAppMessage (doc 06 §2-3, doc 08 §7)."""
from django.db import models


class ConversationStatus(models.TextChoices):
    OPEN = "open", "Aberta"
    HUMAN = "human", "Encaminhada a humano"
    CLOSED = "closed", "Encerrada"


class Direction(models.TextChoices):
    INBOUND = "inbound", "Recebida"
    OUTBOUND = "outbound", "Enviada"


class WhatsAppConversation(models.Model):
    phone = models.CharField(max_length=20, unique=True, verbose_name="telefone")
    patient = models.ForeignKey(
        "patients.Patient",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="whatsapp_conversations",
        verbose_name="paciente",
    )
    laboratory = models.ForeignKey(
        "organizations.Laboratory",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="whatsapp_conversations",
        verbose_name="canal do laboratório",
    )
    provider = models.CharField(
        max_length=24, default="simulator", verbose_name="provedor"
    )  # simulator | whatsapp (G-05)
    status = models.CharField(
        max_length=16, choices=ConversationStatus.choices, default=ConversationStatus.OPEN
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "conversa WhatsApp"
        verbose_name_plural = "conversas WhatsApp"

    def __str__(self) -> str:
        return f"{self.phone} ({self.provider})"


class WhatsAppMessage(models.Model):
    conversation = models.ForeignKey(
        WhatsAppConversation,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="conversa",
    )
    provider_message_id = models.CharField(
        max_length=64, null=True, blank=True, unique=True, verbose_name="id no provedor"
    )
    direction = models.CharField(max_length=16, choices=Direction.choices)
    content = models.TextField(verbose_name="conteúdo")
    ai_interpretation = models.JSONField(null=True, blank=True, verbose_name="interpretação da IA")
    ai_model = models.CharField(max_length=64, blank=True, verbose_name="modelo IA")
    ai_used_mock = models.BooleanField(default=False, verbose_name="usou IA simulada")
    ai_error = models.BooleanField(default=False, verbose_name="erro na IA")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "mensagem WhatsApp"
        verbose_name_plural = "mensagens WhatsApp"

    def __str__(self) -> str:
        return f"{self.direction}: {self.content[:40]}"
