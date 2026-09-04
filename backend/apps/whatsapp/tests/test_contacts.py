"""Testes D-04 — contatos WhatsApp por perfil (BSUID Meta) via API."""

import uuid

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.organizations.models import Laboratory, Pharmacy, Reseller
from apps.technicians.models import Technician
from apps.whatsapp.models import WhatsAppContact

BASE = "/api/v1/whatsapp/contacts"


def _lab(make_user, email="lab-wc@exemplo.com"):
    u = make_user(role_code="laboratory", email=email)
    return u, Laboratory.objects.create(name="Lab Contatos", owner=u)


def _pharmacy(make_user, lab, reseller=None):
    u = make_user(role_code="pharmacy", email=f"farm-{uuid.uuid4().hex[:6]}@exemplo.com")
    return Pharmacy.objects.create(user=u, laboratory=lab, reseller=reseller, name="Farmácia X"), u


def _reseller(make_user, lab):
    u = make_user(role_code="reseller", email=f"rev-{uuid.uuid4().hex[:6]}@exemplo.com")
    return Reseller.objects.create(user=u, laboratory=lab), u


def _technician(make_user, lab, reseller=None):
    u = make_user(role_code="technician", email=f"tec-{uuid.uuid4().hex[:6]}@exemplo.com")
    return Technician.objects.create(user=u, laboratory=lab, reseller=reseller), u


def _client(user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION="Bearer " + str(RefreshToken.for_user(user).access_token))
    return c


def test_laboratory_creates_and_lists_pharmacy_contacts(make_user):
    lab_user, lab = _lab(make_user)
    pharmacy, _ = _pharmacy(make_user, lab)
    client = _client(lab_user)
    first = client.post(
        BASE,
        {
            "pharmacy": pharmacy.pk,
            "number": "+55 11 98888-7777",
            "name": "Farmácia X WhatsApp",
            "meta_bsuid": "@farmacia.x",
        },
        format="json",
    )
    assert first.status_code == 201, first.content
    body = first.json()
    assert body["number"] == "5511988887777"  # normalizado
    assert body["owner_kind"] == "pharmacy"
    second = client.post(
        BASE,
        {
            "pharmacy": pharmacy.pk,
            "number": "5511999990000",
            "name": "Farmácia X 2",
        },
        format="json",
    )
    assert second.status_code == 201  # farmácia aceita lista
    listing = client.get(BASE).json()
    assert len(listing) == 2


def test_technician_single_contact_rule(make_user):
    lab_user, lab = _lab(make_user)
    tech, _ = _technician(make_user, lab)
    client = _client(lab_user)
    ok = client.post(
        BASE,
        {"technician": tech.pk, "number": "5511988881111", "meta_bsuid": "@tec.joao"},
        format="json",
    )
    assert ok.status_code == 201
    dup = client.post(
        BASE,
        {"technician": tech.pk, "number": "5511988882222"},
        format="json",
    )
    assert dup.status_code == 400


def test_owner_must_be_exactly_one_and_validated(make_user):
    lab_user, lab = _lab(make_user)
    client = _client(lab_user)
    missing = client.post(BASE, {"number": "5511988883333"}, format="json")
    assert missing.status_code == 400
    bad_bsuid = client.post(
        BASE,
        {
            "laboratory": lab.pk,
            "number": "5511988883333",
            "meta_bsuid": "sem-arroba",
        },
        format="json",
    )
    assert bad_bsuid.status_code == 400


def test_scope_and_delete(make_user):
    lab_user, lab = _lab(make_user)
    pharmacy, pharmacy_user = _pharmacy(make_user, lab)
    contact = WhatsAppContact.objects.create(pharmacy=pharmacy, number="5511988889999", name="P")
    other_admin, lab2 = _lab(make_user, email="lab2-wc@exemplo.com")
    blocked = _client(other_admin).get(f"{BASE}/{contact.pk}")
    assert blocked.status_code == 403
    # farmácia vê apenas os próprios contatos e pode remover
    farmacia_client = _client(pharmacy_user)
    own = farmacia_client.get(BASE).json()
    assert [c["id"] for c in own] == [contact.pk]
    removed = farmacia_client.delete(f"{BASE}/{contact.pk}")
    assert removed.status_code == 204
    assert WhatsAppContact.objects.filter(pk=contact.pk).count() == 0
