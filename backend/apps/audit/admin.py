from django.contrib import admin

from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "entity_type", "entity_id", "user", "created_at")
    list_filter = ("action", "entity_type", "created_at")
    search_fields = ("entity_type", "entity_id", "user__username")
    readonly_fields = (
        "user",
        "action",
        "entity_type",
        "entity_id",
        "ip",
        "user_agent",
        "metadata",
        "created_at",
    )

    def has_add_permission(self, request):  # trilha é append-only pela UI de admin
        return False

    def has_change_permission(self, request, obj=None):
        return False
