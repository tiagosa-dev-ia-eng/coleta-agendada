from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.accounts import rbac
from apps.audit.models import record as audit_record
from apps.catalog.models import Exam, ExamPrice
from apps.catalog.serializers import ExamPriceWriteSerializer, ExamSerializer
from apps.organizations import scope


class ExamViewSet(GenericViewSet):
    """Catálogo de exames (global) e preço manual por laboratório (G-01)."""

    serializer_class = ExamSerializer
    queryset = Exam.objects.all()

    @staticmethod
    def _is_manager(request):
        return rbac.has_permission(request.user, "user.manage")

    def list(self, request):
        qs = Exam.objects.filter(active=True).order_by("code")
        ctx = {"request": request}
        return Response(self.serializer_class(qs, many=True, context=ctx).data)

    def create(self, request):
        if not self._is_manager(request):
            raise PermissionDenied()
        code = request.data.get("code", "").strip().upper()
        name = request.data.get("name", "").strip()
        if not code or not name:
            return Response(
                {
                    "error": {
                        "code": "invalid",
                        "message": "code e name são obrigatórios.",
                        "details": {},
                    }
                },
                status=400,
            )
        if Exam.objects.filter(code__iexact=code).exists():
            return Response(
                {
                    "error": {
                        "code": "invalid",
                        "message": "Código de exame já existe.",
                        "details": {},
                    }
                },
                status=400,
            )
        exam = Exam.objects.create(code=code, name=name)
        audit_record(
            action="exam.created",
            entity_type="catalog.Exam",
            entity_id=exam.pk,
            user=request.user,
            ip=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            metadata={"code": exam.code},
        )
        ctx = {"request": request}
        return Response(
            self.serializer_class(exam, context=ctx).data,
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, pk=None):
        exam = Exam.objects.filter(pk=pk).first()
        if exam is None:
            raise PermissionDenied()
        ctx = {"request": request}
        return Response(self.serializer_class(exam, context=ctx).data)

    def partial_update(self, request, pk=None):
        """Edição parcial de exame (name/active). Código imutável (referências)."""
        if not self._is_manager(request):
            raise PermissionDenied()
        exam = Exam.objects.filter(pk=pk).first()
        if exam is None:
            raise PermissionDenied()
        payload = {}
        if "name" in request.data:
            name = str(request.data.get("name") or "").strip()
            if not name:
                return Response(
                    {
                        "error": {
                            "code": "invalid",
                            "message": "name não pode ficar vazio.",
                            "details": {},
                        }
                    },
                    status=400,
                )
            payload["name"] = name
        if "active" in request.data:
            payload["active"] = bool(request.data.get("active"))
        if "code" in request.data:
            return Response(
                {
                    "error": {
                        "code": "invalid",
                        "message": "Código do exame é imutável.",
                        "details": {},
                    }
                },
                status=400,
            )
        if payload:
            for key, value in payload.items():
                setattr(exam, key, value)
            exam.save(update_fields=list(payload) + ["updated_at"])
            audit_record(
                action="exam.updated",
                entity_type="catalog.Exam",
                entity_id=exam.pk,
                user=request.user,
                ip=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                metadata={"code": exam.code, "changed": list(payload)},
            )
        ctx = {"request": request}
        return Response(self.serializer_class(exam, context=ctx).data)

    def destroy(self, request, pk=None):
        """Desativa (soft delete) o exame — preços/histórico preservados."""
        if not self._is_manager(request):
            raise PermissionDenied()
        exam = Exam.objects.filter(pk=pk).first()
        if exam is None:
            raise PermissionDenied()
        exam.active = False
        exam.save(update_fields=["active", "updated_at"])
        audit_record(
            action="exam.deactivated",
            entity_type="catalog.Exam",
            entity_id=exam.pk,
            user=request.user,
            ip=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            metadata={"code": exam.code},
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def set_price(self, request, pk=None):
        """Define/atualiza o preço do exame PARA O PRÓPRIO laboratório (G-01)."""
        if not self._is_manager(request):
            raise PermissionDenied()
        lab = scope.laboratory_of(request.user)
        if lab is None:
            raise PermissionDenied("Usuário sem laboratório vinculado.")
        exam = Exam.objects.filter(pk=pk).first()
        if exam is None:
            raise PermissionDenied()
        ser = ExamPriceWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        price_row, _ = ExamPrice.objects.update_or_create(
            laboratory=lab, exam=exam, defaults=ser.validated_data
        )
        audit_record(
            action="exam_price.set",
            entity_type="catalog.ExamPrice",
            entity_id=price_row.pk,
            user=request.user,
            ip=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            metadata={"exam": exam.code, "price": str(price_row.price)},
        )
        return Response(
            {
                "exam_id": exam.pk,
                "price": str(price_row.price),
                "active": price_row.active,
            }
        )
