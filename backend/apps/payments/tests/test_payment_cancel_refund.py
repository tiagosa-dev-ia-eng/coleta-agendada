"""Testes — cancelar e estornar pagamento (endpoints novos)."""


BASE = "/api/v1/payments"


def _approved_request(make_user, auth_client, lab_user):
    from datetime import date, timedelta

    from apps.patients.models import Patient

    p = make_user(role_code="patient", email="pac-pay2@exemplo.com")
    Patient.objects.create(user=p)
    pc = auth_client(p)
    lc = auth_client(lab_user)
    req_id = pc.post(
        "/api/v1/requests",
        {"desired_date": (date.today() + timedelta(days=3)).isoformat()},
        format="json",
    ).json()["id"]
    draft = lc.post(
        f"/api/v1/requests/{req_id}/quotation-draft",
        {"items": [{"exam_code": "HEMO"}]},
        format="json",
    ).json()
    final = lc.post(f"/api/v1/quotations/{draft['id']}/validate", format="json").json()
    lc.post(f"/api/v1/quotations/{final['id']}/send", format="json")
    pc.post(f"/api/v1/quotations/{final['id']}/approve", format="json")
    return p, pc, req_id, lc


def _setup(make_user, auth_client):
    from apps.organizations.models import Laboratory

    lab_user = make_user(role_code="laboratory", email="lab-pay2@exemplo.com")
    Laboratory.objects.create(name="Lab Pay2", owner=lab_user)
    from django.core.management import call_command

    call_command("seed_catalog", verbosity=0)
    return lab_user, auth_client(lab_user)


def test_cancel_link_payment(make_user, auth_client):
    lab_user, lc = _setup(make_user, auth_client)
    _, pc, req_id, lc = _approved_request(make_user, auth_client, lab_user)
    link = lc.post(
        f"/api/v1/requests/{req_id}/payments/link", {"amount": "80.00"}, format="json"
    ).json()
    resp = lc.post(f"{BASE}/{link['id']}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELED"
    # cancelar de novo falha (regra de transição)
    again = lc.post(f"{BASE}/{link['id']}/cancel")
    assert again.status_code == 409


def test_refund_only_confirmed(make_user, auth_client):
    lab_user, lc = _setup(make_user, auth_client)
    _, pc, req_id, lc = _approved_request(make_user, auth_client, lab_user)
    link = lc.post(
        f"/api/v1/requests/{req_id}/payments/link", {"amount": "90.00"}, format="json"
    ).json()
    # link pendente não pode estornar
    early = lc.post(f"{BASE}/{link['id']}/refund")
    assert early.status_code == 409
    # confirma -> estorna
    lc.post(f"{BASE}/{link['id']}/confirm")
    refunded = lc.post(f"{BASE}/{link['id']}/refund")
    assert refunded.status_code == 200
    assert refunded.json()["status"] == "REFUNDED"


def test_patient_cannot_cancel(make_user, auth_client):
    lab_user, lc = _setup(make_user, auth_client)
    _, pc, req_id, lc = _approved_request(make_user, auth_client, lab_user)
    link = lc.post(
        f"/api/v1/requests/{req_id}/payments/link", {"amount": "10.00"}, format="json"
    ).json()
    resp = pc.post(f"{BASE}/{link['id']}/cancel")
    assert resp.status_code == 403
