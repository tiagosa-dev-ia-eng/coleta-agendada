from rest_framework import serializers

from apps.catalog.models import Exam, ExamPrice
from apps.organizations import scope


class ExamSerializer(serializers.ModelSerializer):
    """Exame do catálogo + preço vigente para o laboratório do usuário (G-01)."""

    price = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = ["id", "code", "name", "active", "price"]
        read_only_fields = ["id", "price"]

    def get_price(self, obj):
        request = self.context.get("request")
        if request is None:
            return None
        lab = scope.laboratory_of(request.user)
        if lab is None:
            return None
        row = ExamPrice.objects.filter(laboratory=lab, exam=obj, active=True).first()
        if row is None:
            return None
        return {"id": row.pk, "price": str(row.price)}


class ExamPriceWriteSerializer(serializers.Serializer):
    price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    active = serializers.BooleanField(default=True)

    def validate_price(self, value):
        if value is None or value < 0:
            raise serializers.ValidationError("Preço inválido.")
        return value
