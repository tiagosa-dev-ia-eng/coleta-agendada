from django.contrib import admin

from apps.whatsapp.models import WhatsAppContact, WhatsAppConversation, WhatsAppMessage


@admin.register(WhatsAppConversation)
class WhatsAppConversationAdmin(admin.ModelAdmin):
    list_display = ("phone", "patient", "laboratory", "provider", "status", "updated_at")
    search_fields = ("phone", "patient__user__email")


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "direction", "content", "created_at")
    search_fields = ("conversation__phone",)


@admin.register(WhatsAppContact)
class WhatsAppContactAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "name",
        "meta_bsuid",
        "pharmacy",
        "laboratory",
        "technician",
        "reseller",
    )
    search_fields = ("number", "name", "meta_bsuid")
    list_filter = ("pharmacy__laboratory", "laboratory", "reseller")
