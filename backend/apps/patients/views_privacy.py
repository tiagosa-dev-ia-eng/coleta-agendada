"""Endpoints de privacidade do próprio paciente (B-04/LGPD — escopo MVP).

- consentimento (registro/atualização do consentimento de tratamento);
- exportar dados pessoais (visão consolidada e delimitada);
- anonimização (exclusão lógica: dados identificáveis apagados; registros
  clínicos/financeiros preservados sem identificar o titular).

Retenção física/período de guarda: decisão de política pendente (G-06) —
este MVP não executa purga automática.
"""
import uuid

from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts import rbac
from apps.audit.models import record as audit_record
from apps.patients.models import PatientConsent


def _own_patient(user):
    if user.role_code != rbac.PATIENT:
        raise PermissionDenied("Somente o paciente acessa os próprios dados.")
    patient = getattr(user, "patient_profile", None)
    if patient is None:
        raise PermissionDenied("Cadastro de paciente não localizado.")
    return patient


def _audit(request, action, patient, metadata=None):
    audit_record(
        action=action,
        entity_type="patients.Patient",
        entity_id=patient.pk,
        user=request.user,
        ip=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        metadata=metadata or {},
    )


class PatientConsentView(APIView):
    """POST /patients/me/consent {granted, purpose?} — registro de consentimento."""

    def post(self, request):
        patient = _own_patient(request.user)
        granted = bool(request.data.get("granted", True))
        purpose = str(request.data.get("purpose") or "dados_pessoais_servicos").strip()
        if not purpose:
            purpose = "dados_pessoais_servicos"
        PatientConsent.objects.create(
            patient=patient,
            purpose=purpose,
            granted=granted,
            ip=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        _audit(
            request,
            "patient.consent.updated",
            patient,
            {"granted": granted, "purpose": purpose},
        )
        return Response(
            {
                "status": "ok",
                "patient_id": patient.pk,
                "granted": granted,
                "purpose": purpose,
            },
            status=status.HTTP_201_CREATED,
        )

    def get(self, request):
        patient = _own_patient(request.user)
        rows = patient.consents.order_by("-created_at")
        latest = rows.first()
        return Response(
            {
                "patient_id": patient.pk,
                "latest": (
                    {
                        "granted": latest.granted,
                        "purpose": latest.purpose,
                        "created_at": latest.created_at.isoformat(),
                    }
                    if latest
                    else None
                ),
                "history": [
                    {
                        "granted": c.granted,
                        "purpose": c.purpose,
                        "created_at": c.created_at.isoformat(),
                    }
                    for c in rows[:20]
                ],
            }
        )


class PatientDataExportView(APIView):
    """GET /patients/me/export — consolidação dos dados pessoais do paciente."""

    def get(self, request):
        patient = _own_patient(request.user)
        user = request.user
        agendamentos = []
        for r in patient.requests.all():
            if hasattr(r, "appointment") and r.appointment_id:
                a = r.appointment
                agendamentos.append(
                    {
                        "codigo": a.code,
                        "status": a.status,
                        "quando": a.scheduled_at.isoformat(),
                    }
                )
                if len(agendamentos) >= 50:
                    break
        pagamentos = []
        for r in patient.requests.all():
            for p in r.payments.order_by("-created_at")[:20]:
                pagamentos.append(
                    {
                        "codigo": p.code,
                        "status": p.status,
                        "valor": str(p.amount),
                        "criado_em": p.created_at.isoformat(),
                    }
                )
                if len(pagamentos) >= 100:
                    break
            if len(pagamentos) >= 100:
                break
        export = {
            "usuario": {
                "id": user.pk,
                "nome": user.first_name or user.get_full_name() or None,
                "email": user.email,
                "telefone": user.phone,
            },
            "paciente": {
                "id": patient.pk,
                "nascimento": (
                    patient.birth_date.isoformat() if patient.birth_date else None
                ),
            },
            "solicitacoes": [
                {
                    "protocolo": r.protocol,
                    "status": r.status,
                    "criada_em": r.created_at.isoformat(),
                }
                for r in patient.requests.order_by("-created_at")[:50]
            ],
            "agendamentos": agendamentos,
            "pagamentos": pagamentos,
            "consentimentos": [
                {
                    "granted": c.granted,
                    "purpose": c.purpose,
                    "criado_em": c.created_at.isoformat(),
                }
                for c in patient.consents.order_by("-created_at")[:20]
            ],
        }
        _audit(request, "patient.data_exported", patient, {"bounded": True})
        return Response(export)


class PatientAnonymizeView(APIView):
    """POST /patients/me/anonymize {confirm:"DELETE"} — exclusão lógica (LGPD).

    Remove/anonimiza dados identificáveis (email, telefone, nomes, nascimento,
    usuário inativo); solicitações e registros permanecem sem identificação.
    """

    def post(self, request):
        patient = _own_patient(request.user)
        if request.data.get("confirm") != "DELETE":
            return Response(
                {
                    "error": {
                        "code": "invalid",
                        "message": 'Confirme a exclusão enviando {"confirm": "DELETE"}.',
                        "details": {},
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = request.user
        user.email = f"anonimo-{user.pk}-{uuid.uuid4().hex[:8]}@dados.invalid"
        user.phone = ""
        user.first_name = ""
        user.is_active = False
        user.save(update_fields=["email", "phone", "first_name", "is_active"])
        patient.birth_date = None
        patient.save(update_fields=["birth_date"])
        _audit(
            request,
            "patient.anonymized",
            patient,
            {"user_id": user.pk},
        )
        return Response({"status": "ok", "message": "Dados anonimizados."})
