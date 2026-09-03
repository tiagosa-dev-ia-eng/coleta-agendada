"""Testes M2 — cadastros organizacionais, vínculos e escopo (doc 04 §3-4, doc 14 §3)."""
import pytest

from apps.accounts.models import Role, User
from apps.audit.models import AuditLog
from apps.organizations.models import Laboratory, Pharmacy, Reseller
from apps.patients.models import Patient
from apps.technicians.models import Technician

PASSWORD = "SenhaForte123!"
PHARMACY_PAYLOAD = {
    "name": "Farmácia Saúde",
    "document": "11.222.333/0001-44",
    "city": "São Paulo",
    "state": "SP",
    "email": "farm@exemplo.com",
    "password": PASSWORD,
}
TECH_PAYLOAD = {
    "professional_registration": "COREN 12345",
    "email": "tec@exemplo.com",
    "password": PASSWORD,
}


@pytest.fixture
def lab_user(make_user):
    u = make_user(role_code="laboratory", email="lab@exemplo.com", first_name="Lab")
    lab = Laboratory.objects.create(name="Laboratório Exemplo", owner=u)
    return u, lab


@pytest.fixture
def reseller(lab_user, make_user):
    lab_user, lab = lab_user
    u = make_user(role_code="reseller", email="rev@exemplo.com")
    profile = Reseller.objects.create(user=u, laboratory=lab)
    return u, profile


def _create_pharmacy(client, **over):
    payload = {**PHARMACY_PAYLOAD}
    payload.update(over)
    return client.post("/api/v1/pharmacies", payload, format="json")


def _create_technician(client, **over):
    payload = {**TECH_PAYLOAD}
    payload.update(over)
    return client.post("/api/v1/technicians", payload, format="json")


# ---------------- Laboratory ----------------
def test_laboratory_created_binds_owner(make_user, auth_client):
    u2 = make_user(role_code="laboratory", email="labnovo@exemplo.com")
    resp = auth_client(u2).post(
        "/api/v1/laboratories", {"name": "Lab Novo"}, format="json"
    )
    assert resp.status_code == 201
    created = Laboratory.objects.get(pk=resp.json()["id"])
    assert created.owner == u2
    assert AuditLog.objects.filter(action="laboratory.created").exists()


def test_patient_cannot_create_laboratory(make_user, auth_client):
    p = make_user(role_code="patient", email="p@x.com")
    resp = auth_client(p).post("/api/v1/laboratories", {"name": "X"}, format="json")
    assert resp.status_code == 403


# ---------------- Reseller ----------------
def test_lab_creates_reseller(lab_user, auth_client):
    u, lab = lab_user
    resp = auth_client(u).post(
        "/api/v1/resellers",
        {"email": "rev2@exemplo.com", "password": PASSWORD},
        format="json",
    )
    assert resp.status_code == 201
    profile = Reseller.objects.get(pk=resp.json()["id"])
    assert profile.laboratory == lab
    assert profile.user.role.code == "reseller"


def test_reseller_cannot_create_reseller(reseller, auth_client):
    u, _ = reseller
    resp = auth_client(u).post(
        "/api/v1/resellers", {"email": "outro@exemplo.com", "password": PASSWORD}, format="json"
    )
    assert resp.status_code == 403


# ---------------- Pharmacy ----------------
def test_lab_creates_pharmacy_links_lab(lab_user, auth_client):
    u, lab = lab_user
    resp = _create_pharmacy(auth_client(u))
    assert resp.status_code == 201
    pharmacy = Pharmacy.objects.get(pk=resp.json()["id"])
    assert pharmacy.laboratory == lab
    assert pharmacy.reseller is None
    assert pharmacy.user.role.code == "pharmacy"
    assert AuditLog.objects.filter(action="pharmacy.created", entity_id=pharmacy.pk).exists()


def test_reseller_creates_pharmacy_links_own_network(reseller, auth_client):
    u, profile = reseller
    resp = _create_pharmacy(auth_client(u), email="farm-rev@exemplo.com")
    assert resp.status_code == 201
    pharmacy = Pharmacy.objects.get(pk=resp.json()["id"])
    assert pharmacy.laboratory == profile.laboratory
    assert pharmacy.reseller == profile


def test_pharmacy_scope_lists_only_own_lab(lab_user, auth_client):
    u, lab = lab_user
    _create_pharmacy(auth_client(u), email="f1@exemplo.com")
    # segundo laboratório com farmácia própria
    other_admin = User.objects.create_user(
        email="lab2@exemplo.com", password=PASSWORD, role=Role.objects.get(code="laboratory")
    )
    lab2 = Laboratory.objects.create(name="Lab 2", owner=other_admin)
    _create_pharmacy(auth_client(other_admin), email="f2@exemplo.com")
    resp = auth_client(u).get("/api/v1/pharmacies")
    emails = [p["email_read"] for p in resp.json()]
    assert "f1@exemplo.com" in emails
    assert "f2@exemplo.com" not in emails
    assert lab2.pk != lab.pk


def test_reseller_lists_only_own_indications(reseller, lab_user, auth_client):
    u, profile = reseller
    lab_u, lab = lab_user
    # revendedor indica uma farmácia; laboratório cria outra direto
    _create_pharmacy(auth_client(u), email="ind@exemplo.com")
    _create_pharmacy(auth_client(lab_u), email="direta@exemplo.com")
    resp = auth_client(u).get("/api/v1/pharmacies")
    emails = [p["email_read"] for p in resp.json()]
    assert emails == ["ind@exemplo.com"]


def test_pharmacy_user_cannot_create_another(make_user, auth_client, lab_user):
    lab_u, lab = lab_user
    farm_user = make_user(role_code="pharmacy", email="farmA@exemplo.com")
    Pharmacy.objects.create(
        user=farm_user, laboratory=lab, name="Farm A"
    )
    resp = _create_pharmacy(auth_client(farm_user), email="farmB@exemplo.com")
    assert resp.status_code == 403


def test_pharmacy_reads_own_profile_not_others(make_user, auth_client, lab_user):
    lab_u, lab = lab_user
    a = make_user(role_code="pharmacy", email="fa@exemplo.com")
    b = make_user(role_code="pharmacy", email="fb@exemplo.com")
    pa = Pharmacy.objects.create(user=a, laboratory=lab, name="Farm A")
    pb = Pharmacy.objects.create(user=b, laboratory=lab, name="Farm B")
    client_a = auth_client(a)
    assert client_a.get(f"/api/v1/pharmacies/{pa.pk}").status_code == 200
    assert client_a.get(f"/api/v1/pharmacies/{pb.pk}").status_code == 403


def test_lab_cannot_reuse_existing_email(lab_user, auth_client):
    u, lab = lab_user
    _create_pharmacy(auth_client(u))
    resp = _create_pharmacy(auth_client(u), email="farm@exemplo.com", name="Duplicada")
    assert resp.status_code == 400


# ---------------- Technician ----------------
def test_lab_creates_technician(lab_user, auth_client):
    u, lab = lab_user
    resp = _create_technician(auth_client(u))
    assert resp.status_code == 201
    tech = Technician.objects.get(pk=resp.json()["id"])
    assert tech.laboratory == lab
    assert tech.user.role.code == "technician"
    assert tech.professional_registration == "COREN 12345"


def test_reseller_creates_technician_linked_to_own_network(reseller, auth_client):
    u, profile = reseller
    resp = _create_technician(auth_client(u), email="tec-rev@exemplo.com")
    assert resp.status_code == 201
    tech = Technician.objects.get(pk=resp.json()["id"])
    assert tech.reseller == profile


def test_technician_reads_own_profile(make_user, auth_client, lab_user):
    lab_u, lab = lab_user
    tech_user = make_user(role_code="technician", email="tec1@exemplo.com")
    tech = Technician.objects.create(user=tech_user, laboratory=lab)
    client = auth_client(tech_user)
    assert client.get(f"/api/v1/technicians/{tech.pk}").status_code == 200
    resp = client.get("/api/v1/technicians")
    assert resp.status_code == 403  # listar técnicos exige technician.manage


def test_technician_cannot_create_pharmacy(make_user, auth_client, lab_user):
    lab_u, lab = lab_user
    t = make_user(role_code="technician", email="t@exemplo.com")
    Technician.objects.create(user=t, laboratory=lab)
    resp = _create_pharmacy(auth_client(t), email="x@exemplo.com")
    assert resp.status_code == 403


# ---------------- Patient ----------------
def test_lab_creates_patient(lab_user, auth_client):
    u, _ = lab_user
    resp = auth_client(u).post(
        "/api/v1/patients",
        {"email": "pac@exemplo.com", "password": PASSWORD, "first_name": "Paciente"},
        format="json",
    )
    assert resp.status_code == 201
    patient = Patient.objects.get(pk=resp.json()["id"])
    assert patient.user.role.code == "patient"


def test_patient_reads_own_profile(make_user, auth_client, lab_user):
    lab_u, lab = lab_user
    p = make_user(role_code="patient", email="pp@exemplo.com")
    patient = Patient.objects.create(user=p)
    client = auth_client(p)
    assert client.get(f"/api/v1/patients/{patient.pk}").status_code == 200
    # pacientes não listam pacientes
    assert client.get("/api/v1/patients").status_code == 403
