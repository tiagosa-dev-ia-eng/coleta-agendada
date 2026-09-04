"""Testes — demandas evolutivas: anexos múltiplos de receita (D-05) e resultado (D-06/D-07)."""
import io
from datetime import date, timedelta

from django.core.management import call_command

PNG = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]) + b"0" * 32


def _env(make_user, auth_client):
    from apps.organizations.models import Laboratory

    lab_u = make_user(role_code="laboratory", email="lab-res@exemplo.com")
    lab = Laboratory.objects.create(name="Lab Resultados", owner=lab_u)
    call_command("seed_catalog", verbosity=0)
    patient_u = make_user(role_code="patient", email="pac-res@exemplo.com")
    patient_client = auth_client(patient_u)
    req = patient_client.post(
        "/api/v1/requests",
        {"desired_date": (date.today() + timedelta(days=2)).isoformat()},
        format="json",
    ).json()
    return lab_u, auth_client(lab_u), patient_u, patient_client, req["id"], lab


def _upload(client, req_id, files):
    return client.post(f"/api/v1/requests/{req_id}/attachments", files, format="multipart")


def test_multiple_prescription_files_uploaded(make_user, auth_client):
    lab_u, lc, pu, pc, req_id, lab = _env(make_user, auth_client)
    files = {
        "files": [
            io.BytesIO(PNG),
            io.BytesIO(b"%PDF-1.4 fake"),
        ]
    }
    files["files"][0].name = "receita1.png"
    files["files"][1].name = "receita2.pdf"
    resp = _upload(pc, req_id, files)
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert len(body) == 2
    listing = pc.get(f"/api/v1/requests/{req_id}/medical-orders").json()
    assert len(listing) == 2


def test_upload_rejects_unsupported(make_user, auth_client):
    lab_u, lc, pu, pc, req_id, lab = _env(make_user, auth_client)
    bad = io.BytesIO(b"not an image")
    bad.name = "malware.exe"
    resp = _upload(pc, req_id, {"files": [bad]})
    assert resp.status_code == 400


def test_result_url_register_publish_and_public_page(make_user, auth_client):
    lab_u, lc, pu, pc, req_id, lab = _env(make_user, auth_client)
    # cria sem estado restritivo (solicitação REQUESTED é aceita p/ registro)
    created = lc.post(
        f"/api/v1/requests/{req_id}/results",
        {"result_url": "https://lab.example/resultado/abc", "note": "Hemograma OK"},
        format="json",
    )
    assert created.status_code == 201, created.content
    result = created.json()
    assert result["published"] is False
    assert result["token"]
    # não publicado: 404 público
    pub = pc.get(f"/api/v1/results/{result['token']}")
    assert pub.status_code == 404
    # paciente não publica; laboratório publica
    assert pc.post(f"/api/v1/results/{result['id']}/publish").status_code == 403
    published = lc.post(f"/api/v1/results/{result['id']}/publish", format="json")
    assert published.status_code == 200
    assert published.json()["published"] is True
    # JSON público + página
    pub = pc.get(f"/api/v1/results/{result['token']}").json()
    assert pub["result_url"] == "https://lab.example/resultado/abc"
    page = pc.get(f"/api/v1/results/{result['token']}/page")
    assert page.status_code == 200
    assert "resultado/abc" in page.content.decode()
    # lista da solicitação inclui o resultado
    rows = lc.get(f"/api/v1/requests/{req_id}/results").json()
    assert len(rows) == 1


def test_patient_cannot_register_result(make_user, auth_client):
    lab_u, lc, pu, pc, req_id, lab = _env(make_user, auth_client)
    resp = pc.post(
        f"/api/v1/requests/{req_id}/results",
        {"result_url": "https://x.example/1"},
        format="json",
    )
    assert resp.status_code == 403
