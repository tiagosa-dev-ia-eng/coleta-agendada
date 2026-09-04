"""Serviços de domínio do Local de Coleta (D-03).

Regras (docs/demandas.md D-03): ponto recebe agendamento (disponibilidade =
grade semanal de janelas + estado aberto/fechado), técnico designado pelo
laboratório faz check-in (abrir) / check-out (fechar). Transições auditadas.
"""
from datetime import time

from django.utils import timezone

from apps.audit.models import record as audit_record
from apps.collection_points.models import (
    STATUS_ACTIVE,
    CollectionPointSession,
    TechnicianAssignment,
)


class CollectionPointError(ValueError):
    """Violação de regra de domínio do ponto de coleta."""


class TechnicianNotAssigned(CollectionPointError):
    pass


class PointStateError(CollectionPointError):
    pass


def is_assigned(point, technician):
    """Técnico está designado (ativo) ao ponto?"""
    return (
        TechnicianAssignment.objects.filter(
            point=point, technician=technician, active=True
        ).exists()
        if technician is not None
        else False
    )


def windows_for(point, weekday):
    """Janelas de funcionamento do ponto em um dia da semana (0=segunda)."""
    return list(point.windows.filter(weekday=weekday).order_by("open_time"))


def has_windows(point):
    return point.windows.exists()


def is_within_schedule(point, when):
    """scheduled_at cai em alguma janela semanal do ponto?"""
    from django.utils import timezone

    local = timezone.localtime(when)
    for window in windows_for(point, local.weekday()):
        start = time(window.open_time.hour, window.open_time.minute)
        end = time(window.close_time.hour, window.close_time.minute)
        t = local.time().replace(tzinfo=None)
        if start <= t < end:
            return True
    return False


def check_schedule_availability(point, scheduled_at, *, now=None):
    """Valida a disponibilidade para agendar no ponto (D-03 regra 1 e 2).

    - ponto deve estar ativo;
    - horário deve cair em uma janela semanal (se o ponto tiver janelas);
    - ponto atualmente fechado não recebe agendamento para o dia de hoje
      (estado operacional do técnico não prevê o futuro).
    Lança CollectionPointError com mensagem clara.
    """
    if point.status != STATUS_ACTIVE:
        raise CollectionPointError("Ponto de coleta inativo não recebe agendamento.")
    if not has_windows(point):
        return  # sem grade configurada: comportamento legado (sem restrição)
    if not is_within_schedule(point, scheduled_at):
        raise CollectionPointError(
            "Horário fora do funcionamento do ponto de coleta."
        )
    from django.utils import timezone

    now = now or timezone.now()
    scheduled_day = timezone.localtime(scheduled_at).date()
    if not point.is_open and scheduled_day == timezone.localtime(now).date():
        raise CollectionPointError("Ponto de coleta está fechado hoje.")


def _audit(action, point, *, user=None, metadata=None):
    audit_record(
        action=action,
        entity_type="collection_points.CollectionPoint",
        entity_id=point.pk,
        user=user,
        metadata=metadata or {},
    )


def open_point(point, *, technician, by_user=None):
    """Check-in do técnico: abre o ponto (regra 4). Somente designado ativo."""
    if not is_assigned(point, technician):
        raise TechnicianNotAssigned(
            "Técnico não está designado a este ponto de coleta."
        )
    if point.is_open:
        raise PointStateError("Ponto de coleta já está aberto.")
    session = CollectionPointSession.objects.create(point=point, opened_by=technician)
    point.is_open = True
    point.save(update_fields=["is_open", "updated_at"])
    _audit("collection_point.opened", point, user=by_user, metadata={"session_id": session.pk})
    return session


def close_point(point, *, technician, by_user=None):
    """Check-out do técnico: fecha o ponto (regra 4). Somente designado ativo."""
    if not is_assigned(point, technician):
        raise TechnicianNotAssigned(
            "Técnico não está designado a este ponto de coleta."
        )
    session = point.sessions.filter(closed_at__isnull=True).order_by("-open_at").first()
    if session is None or not point.is_open:
        raise PointStateError("Ponto de coleta não está aberto.")
    session.closed_at = timezone.now()
    session.closed_by = technician
    session.save(update_fields=["closed_at", "closed_by"])
    point.is_open = False
    point.save(update_fields=["is_open", "updated_at"])
    _audit(
        "collection_point.closed",
        point,
        user=by_user,
        metadata={"session_id": session.pk},
    )
    return session


# Dias da semana (Python: 0=segunda..6=domingo) e abreviações pt-BR
WEEKDAY_LABELS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]


def _fmt_time(value):
    return value.strftime("%H:%M")


def schedule_summary(point):
    """Resumo textual da grade semanal, agrupando dias com janelas iguais.

    Ex.: "seg–sex 07:00-12:00, 13:00-19:00; sáb 08:00-12:00".
    """
    grouped = {}
    for weekday in range(7):
        windows = windows_for(point, weekday)
        if not windows:
            continue
        key = tuple(
            (_fmt_time(w.open_time), _fmt_time(w.close_time))
            for w in windows
        )
        grouped.setdefault(key, []).append(weekday)
    if not grouped:
        return "sem horário cadastrado"

    def render_days(days):
        days = sorted(days)
        parts = []
        start = prev = days[0]
        for day in days[1:]:
            if day == prev + 1:
                prev = day
                continue
            parts.append((start, prev))
            start = prev = day
        parts.append((start, prev))
        return ", ".join(
            f"{WEEKDAY_LABELS[a]}-{WEEKDAY_LABELS[b]}" if a != b else WEEKDAY_LABELS[a]
            for a, b in parts
        )

    blocks = []
    for key, days in sorted(grouped.items(), key=lambda item: min(item[1])):
        hours = ", ".join(f"{o}-{c}" for o, c in key)
        blocks.append(f"{render_days(days)} {hours}")
    return "; ".join(blocks)


def open_state_label(point):
    return "aberto agora" if point.is_open else "fechado no momento"
