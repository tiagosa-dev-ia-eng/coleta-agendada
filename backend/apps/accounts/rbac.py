"""Catálogo de papéis e permissões (docs 04 e 16 — RBAC aplicado no backend).

Fonte da matriz funcional: doc 04 §2. Itens marcados com * no doc 04 (inferidos)
foram incluídos como PROPOSTO e devem ser confirmados nos marcos de domínio.
"""
from django.core.exceptions import PermissionDenied

# ---- Códigos de papel (doc 04 §1) ----
LABORATORY = "laboratory"
RESELLER = "reseller"
PHARMACY = "pharmacy"
TECHNICIAN = "technician"
PATIENT = "patient"

ROLES = [
    (LABORATORY, "Laboratório"),
    (RESELLER, "Revendedor"),
    (PHARMACY, "Farmácia"),
    (TECHNICIAN, "Técnico de enfermagem"),
    (PATIENT, "Paciente"),
]

# ---- Catálogo de permissões: (code, nome, módulo) ----
PERMISSION_CATALOG = [
    ("dashboard.view", "Ver dashboard geral", "dashboard"),
    ("reports.view", "Ver relatórios", "reports"),
    ("user.manage", "Gerenciar usuários", "accounts"),
    ("pharmacy.manage", "Cadastrar/gerir farmácias", "organizations"),
    ("technician.manage", "Cadastrar/gerir técnicos", "organizations"),
    ("request.create", "Criar solicitação de coleta", "requests"),
    ("request.view", "Acompanhar solicitações", "requests"),
    ("collection.track", "Acompanhar coletas", "scheduling"),
    ("appointment.manage", "Gerir agenda de coletas", "scheduling"),
    ("collection.execute", "Executar coleta (check-in/out/concluir)", "scheduling"),
    ("quotation.review", "Revisar rascunho de orçamento", "quotations"),
    ("quotation.send", "Enviar orçamento final", "quotations"),
    ("quotation.approve", "Aprovar orçamento", "quotations"),
    ("commission.view", "Consultar comissões", "commissions"),
    ("commission.rule.manage", "Gerir regras de comissão", "commissions"),
    ("whatsapp.attend", "Atender via WhatsApp", "whatsapp"),
    ("audit.view", "Visualizar trilha de auditoria", "audit"),
]

# ---- Permissões por papel (doc 04 §2; * = inferido no doc) ----
ROLE_PERMISSIONS = {
    LABORATORY: [
        "dashboard.view",
        "reports.view",
        "user.manage",
        "pharmacy.manage",
        "technician.manage",
        "request.view",
        "collection.track",
        "quotation.review",
        "quotation.send",
        "commission.view",
        "commission.rule.manage",
        "whatsapp.attend",
        "audit.view",
    ],
    RESELLER: [
        "pharmacy.manage",
        "technician.manage",
        "request.view",
        "collection.track",
        "commission.view",
    ],
    PHARMACY: [
        "appointment.manage",
        "collection.track",
        "commission.view",
        "whatsapp.attend",  # doc 04: atendimento WhatsApp * (inferido)
    ],
    TECHNICIAN: [
        "appointment.manage",
        "collection.execute",
        "commission.view",
        "whatsapp.attend",  # doc 04: atendimento WhatsApp * (inferido)
    ],
    PATIENT: [
        "request.create",
        "request.view",
        "collection.track",
        "quotation.approve",
    ],
}


def role_codes():
    return [code for code, _ in ROLES]


def has_role(user, *codes):
    """True se o usuário tem um dos papéis informados (ou é superusuário)."""
    if user.is_superuser:
        return True
    return bool(user.role and user.role.code in codes)


def has_permission(user, code):
    """True se o usuário possui a permissão (regra persistida por papel)."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if user.role is None:
        return False
    return code in ROLE_PERMISSIONS.get(user.role.code, ())


def ensure_permission(user, code):
    """Levanta PermissionDenied (403) quando o usuário não possui a permissão."""
    if not has_permission(user, code):
        raise PermissionDenied(f"Permissão necessária: {code}")
