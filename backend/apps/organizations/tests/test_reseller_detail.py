"""Testes — retrieve e edição de revendedor (v1.1.5)."""
import uuid

from apps.organizations.models import Laboratory, Reseller

BASE = "/api/v1/resellers"


def _lab_user(make_user):
    u = make_user(role_code="laboratory", email=f"lab-{uuid.uuid4().hex[:6]}@exemplo.com")
    lab = Laboratory.objects.create(name="Lab Reseller", owner=u)
    return u, lab


def test_laboratory_retrieve_and_update_reseller(make_user, auth_client):
    lab_user, lab = _lab_user(make_user)
    res_u = make_user(role_code="reseller", email=f"rev-{uuid.uuid4().hex[:6]}@exemplo.com")
    reseller = Reseller.objects.create(user=res_u, laboratory=lab, status="active")
    client = auth_client(lab_user)
    got = client.get(f"{BASE}/{reseller.pk}")
    assert got.status_code == 200
    assert got.json()["status"] == "active"
    patched = client.patch(f"{BASE}/{reseller.pk}", {"status": "inactive"}, format="json")
    assert patched.status_code == 200
    reseller.refresh_from_db()
    assert reseller.status == "inactive"


def test_reseller_cannot_edit_other(make_user, auth_client):
    lab_user, lab = _lab_user(make_user)
    rev_user = make_user(role_code="reseller", email=f"rev-{uuid.uuid4().hex[:6]}@exemplo.com")
    rev = Reseller.objects.create(user=rev_user, laboratory=lab, status="active")
    other = make_user(role_code="reseller", email=f"rev2-{uuid.uuid4().hex[:6]}@exemplo.com")
    Reseller.objects.create(user=other, laboratory=lab, status="active")
    resp = auth_client(other).patch(f"{BASE}/{rev.pk}", {"status": "inactive"}, format="json")
    assert resp.status_code == 403
