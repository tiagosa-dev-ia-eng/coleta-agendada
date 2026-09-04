"""Local de Coleta (CollectionPoint) — demanda D-03 (docs/demandas.md).

Um "ponto de coleta" é uma entidade de primeiro nível, hospedada por uma
farmácia OU por um laboratório (cada um pode ou não ser ponto de coleta).

Definição de ponto de coleta (usuário, 04/09/2026):
1. recebe agendamento;
2. tem controle de horário de funcionamento (disponibilidade) — grade semanal
   com janelas por dia (OpeningWindow);
3. tem técnico responsável pela abertura e fechamento — designação feita pelo
   laboratório (TechnicianAssignment); o técnico designado faz o
   check-in (abre) e check-out (fecha) do ponto;
4. tem controle de aberto/fechado controlado pelo técnico (CollectionPointSession
   + CollectionPoint.is_open).

Localização/endereço/coordenadas pertencem ao PONTO (usadas pelo chatbot D-01
para indicar o local de coleta mais próximo com horário).
"""
from django.conf import settings
from django.db import models
from django.utils import timezone

STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
STATUS_CHOICES = [
    (STATUS_ACTIVE, "Ativo"),
    (STATUS_INACTIVE, "Inativo"),
]


class PointKind(models.TextChoices):
    PHARMACY = "pharmacy", "Farmácia"
    LABORATORY = "laboratory", "Laboratório"


class Weekday(models.IntegerChoices):
    MONDAY = 0, "Segunda"
    TUESDAY = 1, "Terça"
    WEDNESDAY = 2, "Quarta"
    THURSDAY = 3, "Quinta"
    FRIDAY = 4, "Sexta"
    SATURDAY = 5, "Sábado"
    SUNDAY = 6, "Domingo"


class CollectionPoint(models.Model):
    """Local de coleta hospedado por farmácia (kind=pharmacy) ou laboratório."""

    laboratory = models.ForeignKey(
        "organizations.Laboratory",
        on_delete=models.CASCADE,
        related_name="collection_points",
        verbose_name="laboratório da rede",
    )
    kind = models.CharField(max_length=16, choices=PointKind.choices)
    pharmacy = models.ForeignKey(
        "organizations.Pharmacy",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="collection_points",
        verbose_name="farmácia anfitriã",
    )
    name = models.CharField(max_length=160, verbose_name="nome do ponto")
    address = models.CharField(max_length=255, blank=True, verbose_name="endereço")
    city = models.CharField(max_length=80, blank=True, verbose_name="cidade")
    state = models.CharField(max_length=2, blank=True, verbose_name="UF")
    zip_code = models.CharField(max_length=10, blank=True, verbose_name="CEP")
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="latitude"
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="longitude"
    )
    is_open = models.BooleanField(default=False, verbose_name="aberto agora")
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE, verbose_name="status"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "local de coleta"
        verbose_name_plural = "locais de coleta"
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "pharmacy"],
                condition=models.Q(kind=PointKind.PHARMACY, pharmacy__isnull=False),
                name="uniq_pharmacy_hosted_point",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_kind_display()})"


class OpeningWindow(models.Model):
    """Janela de horário de funcionamento (grade semanal — D-03)."""

    point = models.ForeignKey(
        CollectionPoint, on_delete=models.CASCADE, related_name="windows", verbose_name="ponto"
    )
    weekday = models.PositiveSmallIntegerField(choices=Weekday.choices, verbose_name="dia")
    open_time = models.TimeField(verbose_name="abre")
    close_time = models.TimeField(verbose_name="fecha")

    class Meta:
        ordering = ["weekday", "open_time"]
        verbose_name = "janela de horário"
        verbose_name_plural = "janelas de horário"
        constraints = [
            models.UniqueConstraint(
                fields=["point", "weekday", "open_time", "close_time"],
                name="uniq_window_point_day_time",
            )
        ]

    def __str__(self) -> str:
        return f"{self.get_weekday_display()} {self.open_time:%H:%M}-{self.close_time:%H:%M}"


class TechnicianAssignment(models.Model):
    """Designação de técnico a um ponto de coleta — feita pelo laboratório.

    O técnico designado (ativo) é quem pode abrir (check-in) e fechar
    (check-out) o ponto.
    """

    point = models.ForeignKey(
        CollectionPoint,
        on_delete=models.CASCADE,
        related_name="technician_assignments",
        verbose_name="ponto",
    )
    technician = models.ForeignKey(
        "technicians.Technician",
        on_delete=models.CASCADE,
        related_name="collection_point_assignments",
        verbose_name="técnico",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_technicians_to_points",
        verbose_name="designado por",
    )
    active = models.BooleanField(default=True, verbose_name="designação ativa")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "designação de técnico"
        verbose_name_plural = "designações de técnicos"
        constraints = [
            models.UniqueConstraint(
                fields=["point", "technician"], name="uniq_point_technician_assignment"
            )
        ]

    def __str__(self) -> str:
        return f"{self.technician} → {self.point}"


class CollectionPointSession(models.Model):
    """Sessão de abertura/fechamento do ponto (check-in/check-out do técnico)."""

    point = models.ForeignKey(
        CollectionPoint,
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name="ponto",
    )
    opened_by = models.ForeignKey(
        "technicians.Technician",
        on_delete=models.SET_NULL,
        null=True,
        related_name="opened_point_sessions",
        verbose_name="aberto por",
    )
    open_at = models.DateTimeField(default=timezone.now, verbose_name="aberto em")
    closed_by = models.ForeignKey(
        "technicians.Technician",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="closed_point_sessions",
        verbose_name="fechado por",
    )
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name="fechado em")

    class Meta:
        ordering = ["-open_at"]
        verbose_name = "sessão do ponto de coleta"
        verbose_name_plural = "sessões dos pontos de coleta"

    def __str__(self) -> str:
        state = "aberta" if self.closed_at is None else "fechada"
        return f"{self.point} — {state} ({self.open_at:%d/%m %H:%M})"
