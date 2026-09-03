from apps.accounts import rbac
from apps.organizations.serializers import _EntityBaseSerializer
from apps.technicians.models import Technician


class TechnicianCreateSerializer(_EntityBaseSerializer):
    class Meta:
        model = Technician
        fields = [
            "id",
            "professional_registration",
            "status",
            "email",
            "password",
            "first_name",
            "user_id",
            "email_read",
        ]
        read_only_fields = ["id", "user_id", "email_read"]

    def role_code(self):
        return rbac.TECHNICIAN

    def entity_name(self):
        return "technician"
