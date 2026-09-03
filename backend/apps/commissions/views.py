"""Endpoints de regras e lançamentos de comissão (doc 07 §8)."""
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts import rbac
from apps.audit.models import record as audit_record
from apps.commissions.models import Commission, CommissionRule
from apps.commissions.serializers import CommissionReadSerializer, CommissionRuleSerializer
from apps.commissions.services import CommissionService
from apps.organizations import scope


def _can_manage(user):
    return rbac.has_permission(user, "commission.rule.manage")


def _own_ledgers(user):
    """Extrato escopado por beneficiário (doc 04 §2: consultar comissões)."""
    qs = Commission.objects.select_related("request").order_by("-created_at")
    role = user.role_code
    if user.is_superuser or role == rbac.LABORATORY:
        lab = scope.laboratory_of(user)
        return qs.filter(request__laboratory=lab) if lab else qs.none()
    if role == rbac.PHARMACY:
        prof = getattr(user, "pharmacy_profile", None)
        return qs.filter(beneficiary_type="pharmacy", beneficiary_id=prof.pk) if prof else qs.none()
    if role == rbac.TECHNICIAN:
        prof = getattr(user, "technician_profile", None)
        if prof is None:
            return qs.none()
        return qs.filter(beneficiary_type="technician", beneficiary_id=prof.pk)
    if role == rbac.RESELLER:
        prof = getattr(user, "reseller_profile", None)
        return qs.filter(beneficiary_type="reseller", beneficiary_id=prof.pk) if prof else qs.none()
    return qs.none()


class CommissionRuleListCreateView(APIView):
    """GET lista regras do laboratório; POST cria (commission.rule.manage)."""

    def get(self, request):
        if not (request.user.is_superuser or request.user.role_code == rbac.LABORATORY):
            raise PermissionDenied()
        lab = scope.laboratory_of(request.user)
        qs = CommissionRule.objects.filter(laboratory=lab) if lab else CommissionRule.objects.none()
        return Response(CommissionRuleSerializer(qs, many=True).data)

    def post(self, request):
        if not _can_manage(request.user):
            raise PermissionDenied()
        lab = scope.laboratory_of(request.user)
        if lab is None:
            raise PermissionDenied("Usuário sem laboratório vinculado.")
        ser = CommissionRuleSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        from apps.commissions.models import CommissionRule as _Rule

        rule = _Rule.objects.create(laboratory=lab, **ser.validated_data)
        audit_record(
            action="commission_rule.created",
            entity_type="commissions.CommissionRule",
            entity_id=rule.pk,
            user=request.user,
            ip=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            metadata={"beneficiary": rule.beneficiary_type, "trigger": rule.trigger},
        )
        return Response(CommissionRuleSerializer(rule).data, status=status.HTTP_201_CREATED)


class CommissionRuleUpdateView(APIView):
    """PATCH /commission-rules/{pk} — ajusta regra (lançamentos já usam snapshot)."""

    def patch(self, request, pk=None):
        if not _can_manage(request.user):
            raise PermissionDenied()
        lab = scope.laboratory_of(request.user)
        rule = CommissionRule.objects.filter(pk=pk, laboratory=lab).first()
        if rule is None:
            raise PermissionDenied()
        ser = CommissionRuleSerializer(rule, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        rule = ser.save()
        audit_record(
            action="commission_rule.updated",
            entity_type="commissions.CommissionRule",
            entity_id=rule.pk,
            user=request.user,
            ip=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        return Response(CommissionRuleSerializer(rule).data)


class CommissionListView(APIView):
    """GET /commissions — extrato por beneficiário/perfil (doc 04)."""

    def get(self, request):
        qs = _own_ledgers(request.user)
        return Response(CommissionReadSerializer(qs, many=True).data)


class CommissionDetailView(APIView):
    def get(self, request, pk=None):
        ledger = Commission.objects.filter(pk=pk).first()
        if ledger is None or ledger not in _own_ledgers(request.user):
            raise PermissionDenied()
        return Response(CommissionReadSerializer(ledger).data)


class CommissionMarkPaidView(APIView):
    """POST /commissions/{pk}/mark-paid — financeiro do laboratório."""

    def post(self, request, pk=None):
        if not (request.user.is_superuser or request.user.role_code == rbac.LABORATORY):
            raise PermissionDenied()
        ledger = Commission.objects.filter(pk=pk).first()
        if ledger is None:
            raise PermissionDenied()
        CommissionService.mark_paid(ledger, user=request.user, http_request=request)
        return Response(CommissionReadSerializer(ledger).data)


class CommissionReverseView(APIView):
    """POST /commissions/{pk}/reverse — estorno explícito (doc 10 §7)."""

    def post(self, request, pk=None):
        if not (request.user.is_superuser or request.user.role_code == rbac.LABORATORY):
            raise PermissionDenied()
        ledger = Commission.objects.filter(pk=pk).first()
        if ledger is None:
            raise PermissionDenied()
        CommissionService.reverse(
            ledger,
            user=request.user,
            reason=request.data.get("reason", ""),
            http_request=request,
        )
        return Response(CommissionReadSerializer(ledger).data)
