"""Testes M4 — catálogo e preço por laboratório (decisão G-01)."""
from django.core.management import call_command

from apps.catalog.models import Exam
from apps.organizations.models import Laboratory


def _lab(make_user, name="Lab Preço"):
    u = make_user(role_code="laboratory", email=f"{name.lower().replace(' ', '')}@exemplo.com")
    lab = Laboratory.objects.create(name=name, owner=u)
    call_command("seed_catalog", verbosity=0)  # precifica o primeiro laboratório (o nosso)
    return u, lab


def test_lab_sets_and_reads_own_price(make_user, auth_client):
    u, lab = _lab(make_user)
    client = auth_client(u)
    hem = Exam.objects.get(code="HEMO")
    resp = client.post(f"/api/v1/exams/{hem.pk}/price", {"price": "39.90"}, format="json")
    assert resp.status_code == 200
    assert resp.json()["price"] == "39.90"
    # catálogo com preço do próprio laboratório
    data = client.get("/api/v1/exams").json()
    hem_out = next(x for x in data if x["code"] == "HEMO")
    assert hem_out["price"]["price"] == "39.90"


def test_lab_cannot_see_other_lab_price(make_user, auth_client):
    u1, lab1 = _lab(make_user, name="Lab A")
    u2, lab2 = _lab(make_user, name="Lab B")
    # lab1 altera preço da HEMO
    hem = Exam.objects.get(code="HEMO")
    auth_client(u1).post(f"/api/v1/exams/{hem.pk}/price", {"price": "99.00"}, format="json")
    data = auth_client(u2).get("/api/v1/exams").json()
    hem_out = next(x for x in data if x["code"] == "HEMO")
    assert hem_out["price"] is None  # Lab B não tem preço próprio (G-01: por laboratório)


def test_patient_has_no_price_context(make_user, auth_client):
    p = make_user(role_code="patient", email="p@exemplo.com")
    data = auth_client(p).get("/api/v1/exams").json()
    assert all(x["price"] is None for x in data)


def test_create_duplicate_exam_rejected(make_user, auth_client, monkeypatch):
    u, lab = _lab(make_user)
    resp = auth_client(u).post(
        "/api/v1/exams", {"code": "hemo", "name": "Hemograma"}, format="json"
    )
    assert resp.status_code == 400


def test_non_lab_cannot_create_exam(make_user, auth_client):
    p = make_user(role_code="patient", email="pp@exemplo.com")
    resp = auth_client(p).post("/api/v1/exams", {"code": "X1", "name": "Exame"}, format="json")
    assert resp.status_code == 403
