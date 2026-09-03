"""Testes M7 — comissões (doc 10, ADR-010, gatilhos G-03, CT-INT-006)."""
from datetime import UTC, date, datetime, timedelta

from apps.commissions.models import Commission, CommissionStatus
from apps.organizations.models import Laboratory, Pharmacy, Reseller
from apps.technicians.models import Technician

PASSWORD = "SenhaForte123!"


def _env(make_user):
    from django.core.management import call_command

    lab_u = make_user(role_code="laboratory", email="lab-com@exemplo.com")
    lab = Laboratory.objects.create(name="Lab Comissões", owner=lab_u)
    call_command("seed_catalog", verbosity=0)
    res_u = make_user(role_code="reseller", email="rev-com@exemplo.com")
    res = Reseller.objects.create(user=res_u, laboratory=lab)
    ph_u = make_user(role_code="pharmacy", email="farm-com@exemplo.com")
    pharm = Pharmacy.objects.create(
        user=ph_u, laboratory=lab, reseller=res, name="Farmácia Com", status="active"
    )
    tc_u = make_user(role_code="technician", email="tec-com@exemplo.com")
    tech = Technician.objects.create(user=tc_u, laboratory=lab, reseller=res, status="active")
    return {
        "lab_user": lab_u, "lab": lab, "res": res, "res_user": res_u,
        "pharm": pharm, "pharm_user": ph_u, "tech": tech, "tech_user": tc_u,
    }


def _patient(make_user, auth_client, email="pac-com@exemplo.com"):
    u = make_user(role_code="patient", email=email)
    pc = auth_client(u)
    req = pc.post(
        "/api/v1/requests",
        {"desired_date": (date.today() + timedelta(days=2)).isoformat()},
        format="json",
    ).json()
    return u, pc, req["id"]


def _approve(lc, pc, req_id):
    draft = lc.post(
        f"/api/v1/requests/{req_id}/quotation-draft",
        {"items": [{"exam_code": "HEMO"}]},
        format="json",
    ).json()
    final = lc.post(f"/api/v1/quotations/{draft['id']}/validate", format="json").json()
    lc.post(f"/api/v1/quotations/{final['id']}/send", format="json")
    pc.post(f"/api/v1/quotations/{final['id']}/approve", format="json")


def _rule(lc, **over):
    payload = {
        "beneficiary_type": "reseller",
        "calculation_type": "FIXED",
        "value": "5.00",
        "trigger": "COLLECTION_COMPLETED",
    }
    payload.update(over)
    resp = lc.post("/api/v1/commission-rules", payload, format="json")
    assert resp.status_code == 201, resp.content
    return resp.json()["id"]


def test_fixed_reseller_generated_on_completion(make_user, auth_client):
    env = _env(make_user)
    lc = auth_client(env["lab_user"])
    _rule(lc, beneficiary_type="reseller", calculation_type="FIXED", value="5.00",
          trigger="COLLECTION_COMPLETED")
    _, pc, req_id = _patient(make_user, auth_client)
    _approve(lc, pc, req_id)
    when = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    appt = lc.post(
        f"/api/v1/requests/{req_id}/appointment",
        {"mode": "domiciliary", "scheduled_at": when,
         "technician_id": env["tech"].pk},
        format="json",
    ).json()
    tc = auth_client(env["tech_user"])
    tc.post(f"/api/v1/appointments/{appt['id']}/check-in")
    done = tc.post(f"/api/v1/appointments/{appt['id']}/complete").json()
    assert done["status"] == "COMPLETED"
    ledgers = Commission.objects.filter(request_id=req_id)
    assert ledgers.count() == 1
    row = ledgers.get()
    assert row.beneficiary_type == "reseller"
    assert row.amount == 5  # R$ 5,00 por agendamento (doc 10 §3)
    assert row.status == CommissionStatus.GENERATED
    # idempotente: novo complete não duplica
    tc.post(f"/api/v1/appointments/{appt['id']}/complete")
    assert Commission.objects.filter(request_id=req_id).count() == 1


def test_percentage_technician_on_payment_confirm(make_user, auth_client):
    env = _env(make_user)
    lc = auth_client(env["lab_user"])
    _rule(lc, beneficiary_type="technician", calculation_type="PERCENTAGE",
          value="15.00", trigger="PAYMENT_CONFIRMED")
    _, pc, req_id = _patient(make_user, auth_client)
    _approve(lc, pc, req_id)
    when = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    appt = lc.post(
        f"/api/v1/requests/{req_id}/appointment",
        {"mode": "domiciliary", "scheduled_at": when,
         "technician_id": env["tech"].pk},
        format="json",
    ).json()
    tc = auth_client(env["tech_user"])
    tc.post(f"/api/v1/appointments/{appt['id']}/check-in")
    tc.post(f"/api/v1/appointments/{appt['id']}/complete")
    # pagamento de R$ 100 -> 15% = R$ 15,00 (exemplo doc 10 §3)
    link_resp = lc.post(
        f"/api/v1/requests/{req_id}/payments/link", {"amount": "100.00"}, format="json"
    )
    pay = link_resp.json()
    anon = __import__("rest_framework.test", fromlist=["APIClient"]).APIClient()
    anon.post(
        "/api/v1/payments/webhook",
        {"external_reference": pay["external_reference"], "status": "confirmed"},
        format="json",
    )
    row = Commission.objects.get(request_id=req_id)
    assert row.beneficiary_type == "technician"
    assert row.base_amount == 100
    assert row.amount == 15
    assert row.calculation_type == "PERCENTAGE"


def test_percentage_pharmacy_uses_paid_amount(make_user, auth_client):
    env = _env(make_user)
    lc = auth_client(env["lab_user"])
    _rule(lc, beneficiary_type="pharmacy", calculation_type="PERCENTAGE",
          value="10.00", trigger="PAYMENT_CONFIRMED")
    _, pc, req_id = _patient(make_user, auth_client)
    _approve(lc, pc, req_id)
    when = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    appt = lc.post(
        f"/api/v1/requests/{req_id}/appointment",
        {"mode": "pharmacy", "scheduled_at": when, "pharmacy_id": env["pharm"].pk},
        format="json",
    ).json()
    lc.post(f"/api/v1/appointments/{appt['id']}/check-in")
    lc.post(f"/api/v1/appointments/{appt['id']}/complete")
    link_resp = lc.post(
        f"/api/v1/requests/{req_id}/payments/link", {"amount": "200.00"}, format="json"
    )
    pay = link_resp.json()
    anon = __import__("rest_framework.test", fromlist=["APIClient"]).APIClient()
    anon.post(
        "/api/v1/payments/webhook",
        {"external_reference": pay["external_reference"], "status": "confirmed"},
        format="json",
    )
    row = Commission.objects.get(request_id=req_id)
    assert row.amount == 20  # 10% de 200


def test_rule_edit_does_not_recalculate_ledger(make_user, auth_client):
    env = _env(make_user)
    lc = auth_client(env["lab_user"])
    rule_id = _rule(lc, beneficiary_type="technician", calculation_type="PERCENTAGE",
                    value="15.00", trigger="PAYMENT_CONFIRMED")
    _, pc, req_id = _patient(make_user, auth_client)
    _approve(lc, pc, req_id)
    when = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    appt = lc.post(
        f"/api/v1/requests/{req_id}/appointment",
        {"mode": "domiciliary", "scheduled_at": when, "technician_id": env["tech"].pk},
        format="json",
    ).json()
    tc = auth_client(env["tech_user"])
    tc.post(f"/api/v1/appointments/{appt['id']}/check-in")
    tc.post(f"/api/v1/appointments/{appt['id']}/complete")
    link_resp = lc.post(
        f"/api/v1/requests/{req_id}/payments/link", {"amount": "100.00"}, format="json"
    )
    pay = link_resp.json()
    anon = __import__("rest_framework.test", fromlist=["APIClient"]).APIClient()
    anon.post("/api/v1/payments/webhook",
              {"external_reference": pay["external_reference"], "status": "confirmed"},
              format="json")
    # altera a regra: lançamento NÃO muda (snapshot imutável — ADR-010)
    lc.patch(f"/api/v1/commission-rules/{rule_id}", {"value": "50.00"}, format="json")
    row = Commission.objects.get(request_id=req_id)
    assert row.amount == 15
    assert row.rule_value == 15


def test_mark_paid_and_beneficiary_scope(make_user, auth_client):
    env = _env(make_user)
    lc = auth_client(env["lab_user"])
    _rule(lc, beneficiary_type="reseller", calculation_type="FIXED", value="5.00",
          trigger="COLLECTION_COMPLETED")
    _, pc, req_id = _patient(make_user, auth_client)
    _approve(lc, pc, req_id)
    when = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    appt = lc.post(
        f"/api/v1/requests/{req_id}/appointment",
        {"mode": "domiciliary", "scheduled_at": when, "technician_id": env["tech"].pk},
        format="json",
    ).json()
    tc = auth_client(env["tech_user"])
    tc.post(f"/api/v1/appointments/{appt['id']}/check-in")
    tc.post(f"/api/v1/appointments/{appt['id']}/complete")
    ledger = Commission.objects.get(request_id=req_id)
    paid = lc.post(f"/api/v1/commissions/{ledger.pk}/mark-paid", format="json")
    assert paid.status_code == 200
    assert paid.json()["status"] == "PAID"
    # revendedor vê o próprio extrato
    rev_list = auth_client(env["res_user"]).get("/api/v1/commissions").json()
    assert any(c["id"] == ledger.pk for c in rev_list)
    # farmácia não vê comissão do revendedor
    farm_list = auth_client(env["pharm_user"]).get("/api/v1/commissions").json()
    assert all(c["beneficiary_type"] != "reseller" for c in farm_list)
    assert farm_list == []


def test_non_lab_cannot_create_rule(make_user, auth_client):
    env = _env(make_user)
    p = auth_client(env["pharm_user"])
    resp = p.post(
        "/api/v1/commission-rules",
        {"beneficiary_type": "pharmacy", "calculation_type": "PERCENTAGE",
         "value": "10", "trigger": "PAYMENT_CONFIRMED"},
        format="json",
    )
    assert resp.status_code == 403
