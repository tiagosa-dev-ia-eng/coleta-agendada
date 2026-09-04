"""Testes D-03 — API e operação do Local de Coleta (docs/demandas.md).

Cobre: CRUD com escopo, janelas semanais, designação de técnico pelo
laboratório e abertura/fechamento (check-in/check-out) pelo técnico designado.
"""
import uuid
from datetime import time

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.collection_points import services
from apps.collection_points.models import CollectionPoint, OpeningWindow, PointKind
from apps.organizations.models import Laboratory, Pharmacy, Reseller
from apps.technicians.models import Technician

BASE = "/api/v1/collection-points"


def _lab(make_user, email="lab-cp@exemplo.com"):
    u = make_user(role_code="laboratory", email=email)
    return u, Laboratory.objects.create(name="Lab Pontos", owner=u)


def _pharmacy(make_user, lab, name="Farmácia Central", email=None):
    u = make_user(
        role_code="pharmacy", email=email or f"farm-{uuid.uuid4().hex[:6]}@exemplo.com"
    )
    return Pharmacy.objects.create(user=u, laboratory=lab, name=name), u


def _reseller(make_user, lab):
    u = make_user(role_code="reseller", email=f"rev-{uuid.uuid4().hex[:6]}@exemplo.com")
    return Reseller.objects.create(user=u, laboratory=lab), u


def _technician(make_user, lab):
    u = make_user(
        role_code="technician", email=f"tec-{uuid.uuid4().hex[:6]}@exemplo.com"
    )
    return Technician.objects.create(user=u, laboratory=lab), u


def _client(user):
    c = APIClient()
    c.credentials(
        HTTP_AUTHORIZATION="Bearer " + str(RefreshToken.for_user(user).access_token)
    )
    return c


def _create_point(client, *, kind, pharmacy=None, name="Ponto Teste"):
    payload = {"kind": kind, "name": name}
    if pharmacy is not None:
        payload["pharmacy"] = pharmacy.pk
    return client.post(BASE, payload, format="json")


# ---------- CRUD e regras de host ----------

def test_laboratory_creates_pharmacy_point(make_user):
    lab_user, lab = _lab(make_user)
    pharmacy, _ = _pharmacy(make_user, lab)
    resp = _create_point(_client(lab_user), kind="pharmacy", pharmacy=pharmacy)
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["laboratory"] == lab.pk
    assert body["pharmacy"] == pharmacy.pk
    assert body["is_open"] is False
    assert body["kind"] == "pharmacy"
    # lista escopada do laboratório
    got = _client(lab_user).get(BASE).json()
    assert [p["id"] for p in got] == [body["id"]]


def test_pharmacy_host_cannot_have_two_points(make_user):
    lab_user, lab = _lab(make_user)
    pharmacy, _ = _pharmacy(make_user, lab)
    assert _create_point(_client(lab_user), kind="pharmacy", pharmacy=pharmacy).status_code == 201
    dup = _create_point(_client(lab_user), kind="pharmacy", pharmacy=pharmacy, name="Outro")
    assert dup.status_code == 400
    assert "já é um ponto" in str(dup.json())


def test_laboratory_point_without_pharmacy(make_user):
    lab_user, lab = _lab(make_user)
    ok = _create_point(_client(lab_user), kind="laboratory")
    assert ok.status_code == 201, ok.content
    assert ok.json()["pharmacy"] is None
    # laboratório com farmácia anfitriã é rejeitado
    pharmacy, _ = _pharmacy(make_user, lab)
    bad = _create_point(_client(lab_user), kind="laboratory", pharmacy=pharmacy)
    assert bad.status_code == 400


def test_reseller_manages_own_pharmacy_points_only(make_user):
    lab_user, lab = _lab(make_user)
    reseller, reseller_user = _reseller(make_user, lab)
    pharmacy, _ = _pharmacy(make_user, lab)
    pharmacy.reseller = reseller
    pharmacy.save(update_fields=["reseller"])
    client = _client(reseller_user)
    ok = _create_point(client, kind="pharmacy", pharmacy=pharmacy)
    assert ok.status_code == 201
    lab_kind = _create_point(client, kind="laboratory")
    assert lab_kind.status_code == 403


# ---------- Janelas de horário ----------

def test_windows_add_and_remove(make_user):
    lab_user, lab = _lab(make_user)
    point = CollectionPoint.objects.create(
        laboratory=lab, kind=PointKind.LABORATORY, name="Ponto Lab"
    )
    client = _client(lab_user)
    w1 = client.post(
        f"{BASE}/{point.pk}/windows",
        {"weekday": 0, "open_time": "07:00", "close_time": "12:00"},
        format="json",
    )
    assert w1.status_code == 201
    w2 = client.post(
        f"{BASE}/{point.pk}/windows",
        {"weekday": 0, "open_time": "13:00", "close_time": "19:00"},
        format="json",
    )
    assert w2.status_code == 201
    point.refresh_from_db()
    assert point.windows.count() == 2
    assert services.schedule_summary(point) == "seg 07:00-12:00, 13:00-19:00"
    wid = point.windows.first().pk
    removed = client.delete(f"{BASE}/{point.pk}/windows/{wid}")
    assert removed.status_code == 200
    assert point.windows.count() == 1


def test_schedule_summary_groups_consecutive_days(make_user):
    lab_user, lab = _lab(make_user)
    point = CollectionPoint.objects.create(
        laboratory=lab, kind=PointKind.LABORATORY, name="Ponto Horário"
    )
    for weekday in range(5):  # seg-sex iguais
        OpeningWindow.objects.create(
            point=point, weekday=weekday, open_time=time(7), close_time=time(12)
        )
        OpeningWindow.objects.create(
            point=point, weekday=weekday, open_time=time(13), close_time=time(19)
        )
    OpeningWindow.objects.create(
        point=point, weekday=5, open_time=time(8), close_time=time(12)
    )
    summary = services.schedule_summary(point)
    assert summary == "seg-sex 07:00-12:00, 13:00-19:00; sáb 08:00-12:00"


# ---------- Designação de técnico (laboratório) ----------

def test_assign_and_unassign_technician(make_user):
    lab_user, lab = _lab(make_user)
    pharmacy, _ = _pharmacy(make_user, lab)
    point = CollectionPoint.objects.create(
        laboratory=lab,
        kind=PointKind.PHARMACY,
        pharmacy=pharmacy,
        name="Ponto Farmácia",
    )
    tech, _ = _technician(make_user, lab)
    client = _client(lab_user)
    assigned = client.post(
        f"{BASE}/{point.pk}/technicians", {"technician_id": tech.pk}, format="json"
    )
    assert assigned.status_code == 200
    point.refresh_from_db()
    assert services.is_assigned(point, tech)
    removed = client.delete(f"{BASE}/{point.pk}/technicians/{tech.pk}")
    assert removed.status_code == 200
    point.refresh_from_db()
    assert not services.is_assigned(point, tech)


def test_only_laboratory_designates_technicians(make_user):
    lab_user, lab = _lab(make_user)
    pharmacy, pharmacy_user = _pharmacy(make_user, lab)
    point = CollectionPoint.objects.create(
        laboratory=lab, kind=PointKind.PHARMACY, pharmacy=pharmacy, name="Ponto"
    )
    tech, _ = _technician(make_user, lab)
    blocked = _client(pharmacy_user).post(
        f"{BASE}/{point.pk}/technicians", {"technician_id": tech.pk}, format="json"
    )
    assert blocked.status_code == 403
    other_admin, lab2 = _lab(make_user, email="lab2-cp@exemplo.com")
    foreign_tech, _ = _technician(make_user, lab2)
    foreign = _client(lab_user).post(
        f"{BASE}/{point.pk}/technicians",
        {"technician_id": foreign_tech.pk},
        format="json",
    )
    assert foreign.status_code == 400


# ---------- Abertura/fechamento pelo técnico designado ----------

def _ready_point_with_technician(make_user, lab_user, lab):
    pharmacy, _ = _pharmacy(make_user, lab)
    point = CollectionPoint.objects.create(
        laboratory=lab, kind=PointKind.PHARMACY, pharmacy=pharmacy, name="Ponto Ops"
    )
    tech, tech_user = _technician(make_user, lab)
    _client(lab_user).post(
        f"{BASE}/{point.pk}/technicians", {"technician_id": tech.pk}, format="json"
    )
    return point, tech, tech_user


def test_open_close_lifecycle_by_designated_technician(make_user):
    lab_user, lab = _lab(make_user)
    point, tech, tech_user = _ready_point_with_technician(make_user, lab_user, lab)
    other_tech, other_tech_user = _technician(make_user, lab)
    # técnico não designado não opera
    denied = _client(other_tech_user).post(f"{BASE}/{point.pk}/open")
    assert denied.status_code == 403
    client = _client(tech_user)
    opened = client.post(f"{BASE}/{point.pk}/open")
    assert opened.status_code == 200
    assert opened.json()["is_open"] is True
    assert point.sessions.count() == 1
    # já aberto -> 409
    again = client.post(f"{BASE}/{point.pk}/open")
    assert again.status_code == 409
    closed = client.post(f"{BASE}/{point.pk}/close")
    assert closed.status_code == 200
    assert closed.json()["is_open"] is False
    twice = client.post(f"{BASE}/{point.pk}/close")
    assert twice.status_code == 409
    # auditoria registrada
    from apps.audit.models import AuditLog

    actions = AuditLog.objects.filter(entity_type="collection_points.CollectionPoint").values_list(
        "action", flat=True
    )
    assert "collection_point.opened" in actions
    assert "collection_point.closed" in actions


def test_technician_sees_only_assigned_points(make_user):
    lab_user, lab = _lab(make_user)
    point, _, tech_user = _ready_point_with_technician(make_user, lab_user, lab)
    other_lab_admin, lab2 = _lab(make_user, email="lab3-cp@exemplo.com")
    other_pharm, _ = _pharmacy(make_user, lab2)
    CollectionPoint.objects.create(
        laboratory=lab2, kind=PointKind.PHARMACY, pharmacy=other_pharm, name="Outro Lab"
    )
    listing = _client(tech_user).get(BASE).json()
    assert [p["id"] for p in listing] == [point.pk]
