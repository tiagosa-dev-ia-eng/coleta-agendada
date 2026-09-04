"""WhatsAppConversation e WhatsAppMessage (doc 06 §2-3, doc 08 §7)."""
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.whatsapp.validators import normalize_phone_digits, validate_meta_bsuid


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


class WhatsAppContact(models.Model):
    """Contato de WhatsApp de um perfil — demanda D-04 (docs/demandas.md).

    Padrão da Meta (BSUID): número + nome de exibição (+ @<nome usuário>
    quando aplicável). Técnico e revenda possuem 1 número/nome; farmácia e
    laboratório possuem LISTA de números/nomes de contato. Exatamente um
    dos perfis deve estar preenchido (validado no serializer/serviço).
    """

    pharmacy = models.ForeignKey(
        "organizations.Pharmacy",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="whatsapp_contacts",
        verbose_name="farmácia",
    )
    laboratory = models.ForeignKey(
        "organizations.Laboratory",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="whatsapp_contacts",
        verbose_name="laboratório",
    )
    technician = models.ForeignKey(
        "technicians.Technician",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="whatsapp_contacts",
        verbose_name="técnico",
    )
    reseller = models.ForeignKey(
        "organizations.Reseller",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="whatsapp_contacts",
        verbose_name="revenda",
    )
    number = models.CharField(max_length=20, unique=True, verbose_name="número WhatsApp")
    name = models.CharField(max_length=120, blank=True, verbose_name="nome de exibição")
    meta_bsuid = models.CharField(
        max_length=120,
        blank=True,
        validators=[validate_meta_bsuid],
        verbose_name="BSUID (Meta)",
        help_text='Handle da Meta, ex.: "@nome.usuario".',
    )
    is_main = models.BooleanField(default=False, verbose_name="principal")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "contato WhatsApp"
        verbose_name_plural = "contatos WhatsApp"

    def __str__(self) -> str:
        owner = "?"
        if self.pharmacy_id:
            owner = self.pharmacy.name
        elif self.laboratory_id:
            owner = self.laboratory.name
        elif self.technician_id:
            owner = str(self.technician)
        elif self.reseller_id:
            owner = str(self.reseller)
        label = self.name or self.meta_bsuid or self.number
        return f"{owner}: {label} ({self.number})"

    def clean(self):
        super().clean()
        owners = [
            bool(self.pharmacy_id or self.pharmacy),
            bool(self.laboratory_id or self.laboratory),
            bool(self.technician_id or self.technician),
            bool(self.reseller_id or self.reseller),
        ]
        if sum(owners) != 1:
            raise ValidationError(
                _(
                    "O contato deve pertencer a exatamente um perfil "
                    "(farmácia, laboratório, técnico ou revenda)."
                )
            )
        self.number = normalize_phone_digits(self.number)
        if not self.number:
            raise ValidationError(_("Número de WhatsApp inválido."))
