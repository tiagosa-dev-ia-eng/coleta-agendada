"""Testes M5 — agendamento e realização (CT-INT-003/004/005; doc 14 §2)."""
import uuid
from datetime import UTC, date, datetime, time, timedelta

from django.core.management import call_command

from apps.collection_points.models import CollectionPoint
from apps.organizations.models import Laboratory, Pharmacy
from apps.technicians.models import Technician


def _lab(make_user):
    u = make_user(role_code="laboratory", email="lab-agen@exemplo.com")
    lab = Laboratory.objects.create(name="Lab Agendamento", owner=u)
    call_command("seed_catalog", verbosity=0)
    return u, lab


def _pharmacy(make_user, lab):
    u = make_user(role_code="pharmacy", email="farm-agen@exemplo.com")
    pharm = Pharmacy.objects.create(
        user=u, laboratory=lab, name="Farmácia Central", status="active"
    )
    # D-03: farmácia vira ponto de coleta (recebe agendamento)
    CollectionPoint.objects.create(
        laboratory=lab, kind="pharmacy", pharmacy=pharm, name=pharm.name
    )
    return pharm, u


def _technician(make_user, lab):
    u = make_user(
        role_code="technician", email=f"tec-agen-{uuid.uuid4().hex[:6]}@exemplo.com"
    )
    return Technician.objects.create(user=u, laboratory=lab, status="active"), u


def _approved_request(make_user, auth_client, lab, email="pac-agen@exemplo.com"):
    """Paciente cria solicitação e percorre draft->validate->send->approve."""
    p = make_user(role_code="patient", email=email)
    pclient = auth_client(p)
    lclient = auth_client(lab)
    req_id = pclient.post(
        "/api/v1/requests",
        {
            "desired_date": (date.today() + timedelta(days=2)).isoformat(),
            "collection_mode": "pharmacy",
        },
        format="json",
    ).json()["id"]
    draft = lclient.post(
        f"/api/v1/requests/{req_id}/quotation-draft",
        {"items": [{"exam_code": "HEMO"}]},
        format="json",
    ).json()
    final = lclient.post(f"/api/v1/quotations/{draft['id']}/validate", format="json").json()
    lclient.post(f"/api/v1/quotations/{final['id']}/send", format="json")
    pclient.post(f"/api/v1/quotations/{final['id']}/approve", format="json")
    return p, pclient, req_id, lclient


def _when():
    return (datetime.now(UTC) + timedelta(days=2)).isoformat()


def test_schedule_pharmacy_appointment(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    pharmacy, _ = _pharmacy(make_user, lab)
    _, pclient, req_id, lclient = _approved_request(make_user, auth_client, lab_user)
    resp = lclient.post(
        f"/api/v1/requests/{req_id}/appointment",
        {"mode": "pharmacy", "scheduled_at": _when(), "pharmacy_id": pharmacy.pk},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["code"].startswith("AP-")
    assert body["status"] == "SCHEDULED"
    assert body["pharmacy_name"] == "Farmácia Central"
    # paciente vê o agendamento na própria agenda
    agenda = pclient.get("/api/v1/appointments").json()
    assert any(a["id"] == body["id"] for a in agenda)


def test_schedule_domiciliary_requires_technician(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    tech, _ = _technician(make_user, lab)
    _, _, req_id, lclient = _approved_request(make_user, auth_client, lab_user)
    resp = lclient.post(
        f"/api/v1/requests/{req_id}/appointment",
        {"mode": "domiciliary", "scheduled_at": _when(), "technician_id": tech.pk},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "SCHEDULED"
    # agenda do técnico lista o agendamento
    tech_agenda = auth_client(tech.user).get("/api/v1/appointments").json()
    assert any(a["id"] == resp.json()["id"] for a in tech_agenda)


def test_cannot_schedule_before_approval(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    pharmacy, _ = _pharmacy(make_user, lab)
    p = make_user(role_code="patient", email="px@exemplo.com")
    pclient = auth_client(p)
    lclient = auth_client(lab_user)
    req_id = pclient.post(
        "/api/v1/requests", {"collection_mode": "pharmacy"}, format="json"
    ).json()["id"]
    resp = lclient.post(
        f"/api/v1/requests/{req_id}/appointment",
        {"mode": "pharmacy", "scheduled_at": _when(), "pharmacy_id": pharmacy.pk},
        format="json",
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "scheduling_error"


def test_duplicate_schedule_rejected(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    pharmacy, _ = _pharmacy(make_user, lab)
    _, _, req_id, lclient = _approved_request(make_user, auth_client, lab_user)
    payload = {"mode": "pharmacy", "scheduled_at": _when(), "pharmacy_id": pharmacy.pk}
    first = lclient.post(f"/api/v1/requests/{req_id}/appointment", payload, format="json")
    assert first.status_code == 201
    resp = lclient.post(f"/api/v1/requests/{req_id}/appointment", payload, format="json")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "appointment_exists"


def test_foreign_pharmacy_rejected(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    other_admin = make_user(role_code="laboratory", email="lab2-agen@exemplo.com")
    lab2 = Laboratory.objects.create(name="Lab 2 Agendamento", owner=other_admin)
    farm2_user = make_user(role_code="pharmacy", email="farm2@exemplo.com")
    Pharmacy.objects.create(user=farm2_user, laboratory=lab2, name="Farmácia 2")
    _, _, req_id, lclient = _approved_request(make_user, auth_client, lab_user)
    resp = lclient.post(
        f"/api/v1/requests/{req_id}/appointment",
        {
            "mode": "pharmacy",
            "scheduled_at": _when(),
            "pharmacy_id": Pharmacy.objects.get(name="Farmácia 2").pk,
        },
        format="json",
    )
    assert resp.status_code == 400


def test_checkin_and_complete_without_payment(make_user, auth_client):
    """CT-INT-005: concluir a coleta não depende de pagamento (ADR-008)."""
    lab_user, lab = _lab(make_user)
    tech, tech_user = _technician(make_user, lab)
    _, pclient, req_id, lclient = _approved_request(make_user, auth_client, lab_user)
    appt_id = lclient.post(
        f"/api/v1/requests/{req_id}/appointment",
        {"mode": "domiciliary", "scheduled_at": _when(), "technician_id": tech.pk},
        format="json",
    ).json()["id"]
    tclient = auth_client(tech_user)
    # outro técnico não executa
    other_tech = make_user(role_code="technician", email="tec-outro@exemplo.com")
    Technician.objects.create(user=other_tech, laboratory=lab)
    blocked = auth_client(other_tech).post(f"/api/v1/appointments/{appt_id}/check-in")
    assert blocked.status_code == 403
    # técnico atribuído: check-in -> IN_PROGRESS
    ci = tclient.post(f"/api/v1/appointments/{appt_id}/check-in")
    assert ci.status_code == 200
    assert ci.json()["checkin_at"] is not None
    # conclusão SEM pagamento (não existe Payment no M5 e o domínio não exige)
    done = tclient.post(f"/api/v1/appointments/{appt_id}/complete")
    assert done.status_code == 200
    assert done.json()["status"] == "COMPLETED"
    assert done.json()["completed_at"] is not None
    # histórico percorrido sem etapa de pagamento (ADR-008)
    hist = pclient.get(f"/api/v1/requests/{req_id}/history").json()
    states = [h["to_status"] for h in hist]
    assert states[-1] == "COMPLETED"
    assert "PAYMENT_PENDING" not in states


def test_agenda_scoped_per_profile(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    pharm1, pharm1_user = _pharmacy(make_user, lab)
    tech1, tech1_user = _technician(make_user, lab)
    # duas solicitações aprovadas: uma na farmácia, uma domiciliar
    _, p1, r1, lc1 = _approved_request(make_user, auth_client, lab_user, email="pa1@exemplo.com")
    _, p2, r2, lc2 = _approved_request(make_user, auth_client, lab_user, email="pa2@exemplo.com")
    a1 = lc1.post(
        f"/api/v1/requests/{r1}/appointment",
        {"mode": "pharmacy", "scheduled_at": _when(), "pharmacy_id": pharm1.pk},
        format="json",
    ).json()["id"]
    a2 = lc2.post(
        f"/api/v1/requests/{r2}/appointment",
        {"mode": "domiciliary", "scheduled_at": _when(), "technician_id": tech1.pk},
        format="json",
    ).json()["id"]
    # farmácia só vê a dela; técnico só o dele
    pharm_agenda = auth_client(pharm1_user).get("/api/v1/appointments").json()
    assert [x["id"] for x in pharm_agenda] == [a1]
    tech_agenda = auth_client(tech1_user).get("/api/v1/appointments").json()
    assert [x["id"] for x in tech_agenda] == [a2]
    # paciente 1 não vê agendamento do paciente 2
    assert p1.get(f"/api/v1/appointments/{a2}").status_code == 403


# ---------- D-03: agendamento respeita disponibilidade do ponto ----------

def _next_at_10am(days_ahead):
    target = datetime.now(UTC) + timedelta(days=days_ahead)
    return target.replace(hour=10, minute=0, second=0, microsecond=0)


def _full_day_window(point, weekday):
    from apps.collection_points.models import OpeningWindow

    OpeningWindow.objects.create(
        point=point, weekday=weekday, open_time=time(0, 0), close_time=time(23, 59, 59)
    )


def test_pharmacy_must_host_active_point(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    p_user = make_user(role_code="pharmacy", email="farm-semponto@exemplo.com")
    Pharmacy.objects.create(user=p_user, laboratory=lab, name="Sem Ponto", status="active")
    _, _, req_id, lclient = _approved_request(make_user, auth_client, lab_user)
    when = _when()
    resp = lclient.post(
        f"/api/v1/requests/{req_id}/appointment",
        {"mode": "pharmacy", "scheduled_at": when, "pharmacy_id": p_user.pharmacy_profile.pk},
        format="json",
    )
    assert resp.status_code == 409
    assert "ponto de coleta" in resp.json()["error"]["message"]


def test_schedule_inside_window_is_allowed(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    pharmacy, _ = _pharmacy(make_user, lab)
    point = CollectionPoint.objects.get(pharmacy=pharmacy)
    when = _next_at_10am(2)
    _full_day_window(point, when.weekday())
    _, _, req_id, lclient = _approved_request(make_user, auth_client, lab_user)
    resp = lclient.post(
        f"/api/v1/requests/{req_id}/appointment",
        {"mode": "pharmacy", "scheduled_at": when.isoformat(), "pharmacy_id": pharmacy.pk},
        format="json",
    )
    assert resp.status_code == 201, resp.content


def test_schedule_outside_window_rejected(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    pharmacy, _ = _pharmacy(make_user, lab)
    point = CollectionPoint.objects.get(pharmacy=pharmacy)
    when = _next_at_10am(2)
    # janela apenas em outro dia da semana
    _full_day_window(point, (when.weekday() + 1) % 7)
    _, _, req_id, lclient = _approved_request(make_user, auth_client, lab_user)
    resp = lclient.post(
        f"/api/v1/requests/{req_id}/appointment",
        {"mode": "pharmacy", "scheduled_at": when.isoformat(), "pharmacy_id": pharmacy.pk},
        format="json",
    )
    assert resp.status_code == 409
    assert "funcionamento" in resp.json()["error"]["message"]


def test_schedule_closed_today_rejected(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    pharmacy, _ = _pharmacy(make_user, lab)
    point = CollectionPoint.objects.get(pharmacy=pharmacy)
    when = datetime.now(UTC).replace(hour=10, minute=0, second=0, microsecond=0)
    _full_day_window(point, when.weekday())
    # ponto nasce fechado (is_open=False) e segue fechado hoje
    _, _, req_id, lclient = _approved_request(make_user, auth_client, lab_user)
    resp = lclient.post(
        f"/api/v1/requests/{req_id}/appointment",
        {"mode": "pharmacy", "scheduled_at": when.isoformat(), "pharmacy_id": pharmacy.pk},
        format="json",
    )
    assert resp.status_code == 409
    assert "fechado hoje" in resp.json()["error"]["message"]


# ---------- v1.1.10: agenda sem conflito (janela de coleta) ----------

def test_pharmacy_slot_conflict_rejected(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    pharmacy, _ = _pharmacy(make_user, lab)
    when = _next_at_10am(3)
    _, _, req1, lc = _approved_request(make_user, auth_client, lab_user, email="pac-c1@exemplo.com")
    _, _, req2, lc2 = _approved_request(
        make_user, auth_client, lab_user, email="pac-c2@exemplo.com"
    )
    payload = {"mode": "pharmacy", "scheduled_at": when.isoformat(), "pharmacy_id": pharmacy.pk}
    first = lc.post(f"/api/v1/requests/{req1}/appointment", payload, format="json")
    assert first.status_code == 201, first.content
    # mesma farmácia, 10 minutos depois (dentro da janela de 30 min) -> conflito
    second = lc.post(f"/api/v1/requests/{req2}/appointment", payload, format="json")
    assert second.status_code == 409
    assert "Conflito de agenda" in second.json()["error"]["message"]
    # horário seguinte fora da janela (10:30) é aceito
    later = _next_at_10am(3).replace(hour=10, minute=30)
    ok = lc.post(
        f"/api/v1/requests/{req2}/appointment",
        {"mode": "pharmacy", "scheduled_at": later.isoformat(), "pharmacy_id": pharmacy.pk},
        format="json",
    )
    assert ok.status_code == 201, ok.content


def test_technician_slot_conflict_domiciliary(make_user, auth_client):
    lab_user, lab = _lab(make_user)
    tech, _ = _technician(make_user, lab)
    when = _next_at_10am(3)
    _, _, req1, lc = _approved_request(make_user, auth_client, lab_user, email="pac-d1@exemplo.com")
    _, _, req2, lc2 = _approved_request(
        make_user, auth_client, lab_user, email="pac-d2@exemplo.com"
    )
    payload = {"mode": "domiciliary", "scheduled_at": when.isoformat(), "technician_id": tech.pk}
    created = lc.post(
        f"/api/v1/requests/{req1}/appointment", payload, format="json"
    )
    assert created.status_code == 201
    conflict = lc.post(f"/api/v1/requests/{req2}/appointment", payload, format="json")
    assert conflict.status_code == 409
    # outro técnico no mesmo horário é aceito
    other_tech, _ = _technician(make_user, lab)
    free = lc.post(
        f"/api/v1/requests/{req2}/appointment",
        {
            "mode": "domiciliary",
            "scheduled_at": when.isoformat(),
            "technician_id": other_tech.pk,
        },
        format="json",
    )
    assert free.status_code == 201
