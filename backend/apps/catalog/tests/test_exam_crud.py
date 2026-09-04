"""Testes — CRUD do catálogo de exames (G-01): retrieve/edição/desativação."""

from apps.catalog.models import Exam

BASE = "/api/v1/exams"


def _seed(make_user, auth_client):
    from django.core.management import call_command

    lab_user = make_user(role_code="laboratory", email="lab-exam@exemplo.com")
    call_command("seed_catalog", verbosity=0)
    return lab_user, auth_client(lab_user)


def test_exam_retrieve_and_update(make_user, auth_client):
    lab_user, client = _seed(make_user, auth_client)
    exam = Exam.objects.get(code="HEMO")
    got = client.get(f"{BASE}/{exam.pk}")
    assert got.status_code == 200
    assert got.json()["code"] == "HEMO"
    patched = client.patch(f"{BASE}/{exam.pk}", {"name": "Hemograma (atualizado)"}, format="json")
    assert patched.status_code == 200
    exam.refresh_from_db()
    assert exam.name == "Hemograma (atualizado)"


def test_exam_code_immutable_and_deactivate(make_user, auth_client):
    _, client = _seed(make_user, auth_client)
    exam = Exam.objects.get(code="GLI")
    locked = client.patch(f"{BASE}/{exam.pk}", {"code": "XYZ"}, format="json")
    assert locked.status_code == 400
    removed = client.delete(f"{BASE}/{exam.pk}")
    assert removed.status_code == 204
    exam.refresh_from_db()
    assert exam.active is False
    # exame inativo some da listagem ativa
    listing = client.get(BASE).json()
    assert all(item["code"] != "GLI" for item in listing)


def test_non_manager_cannot_edit(make_user, auth_client):
    patient = make_user(role_code="patient", email="pac-exam@exemplo.com")
    client = auth_client(patient)
    exam = Exam.objects.create(code="TST1", name="Teste")
    resp = client.patch(f"{BASE}/{exam.pk}", {"name": "X"}, format="json")
    assert resp.status_code == 403
    resp = client.delete(f"{BASE}/{exam.pk}")
    assert resp.status_code == 403
