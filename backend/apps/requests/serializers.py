from rest_framework import serializers

from apps.patients.models import Patient
from apps.requests.models import CollectionRequest, MedicalOrder
from apps.requests.statuses import CollectionMode, DesiredPeriod


class CollectionRequestSerializer(serializers.ModelSerializer):
    patient = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    medical_orders_count = serializers.IntegerField(source="medical_orders.count", read_only=True)
    status_history = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CollectionRequest
        fields = [
            "id",
            "protocol",
            "patient",
            "desired_date",
            "desired_period",
            "collection_mode",
            "preferred_location",
            "status",
            "status_display",
            "notes",
            "medical_orders_count",
            "created_at",
            "updated_at",
            "status_history",
        ]
        read_only_fields = [
            "id",
            "protocol",
            "status",
            "status_display",
            "created_at",
            "updated_at",
        ]

    def get_patient(self, obj):
        patient = obj.patient
        user = patient.user
        return {
            "id": patient.pk,
            "name": user.full_name,
            "email": user.email,
            "document": user.document,
        }

    def get_status_history(self, obj):
        history = getattr(obj, "_history", None)
        if history is None:
            return []
        return [
            {
                "from_status": h.from_status,
                "to_status": h.to_status,
                "origin": h.origin,
                "reason": h.reason,
                "created_at": h.created_at.isoformat(),
            }
            for h in history
        ]


class CollectionRequestCreateSerializer(serializers.Serializer):
    desired_date = serializers.DateField(required=False, allow_null=True)
    desired_period = serializers.ChoiceField(choices=DesiredPeriod.choices, required=False)
    collection_mode = serializers.ChoiceField(
        choices=CollectionMode.choices, default=CollectionMode.PHARMACY
    )
    preferred_location = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        from apps.requests.services import RequestStateService

        user = self.context["request"].user
        # auto-provisiona o perfil do paciente na primeira solicitação (demo/dev)
        patient, _ = Patient.objects.get_or_create(user=user)
        request_obj = CollectionRequest.objects.create(patient=patient, **validated_data)
        RequestStateService.mark_created(request_obj, changed_by=user, origin="user")
        return request_obj


class MedicalOrderSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = MedicalOrder
        fields = ["id", "original_name", "mime_type", "size", "url", "uploaded_at"]
        read_only_fields = fields

    def get_url(self, obj):
        request = self.context.get("request")
        if request is None:
            return obj.file.url
        return request.build_absolute_uri(obj.file.url)
