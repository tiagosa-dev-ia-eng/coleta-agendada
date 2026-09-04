from django.contrib import admin

from apps.organizations.models import Laboratory, Pharmacy, Reseller


@admin.register(Laboratory)
class LaboratoryAdmin(admin.ModelAdmin):
    list_display = ("name", "document", "owner", "status")
    search_fields = ("name", "document")


@admin.register(Reseller)
class ResellerAdmin(admin.ModelAdmin):
    list_display = ("user", "laboratory", "status")
    list_filter = ("laboratory",)


@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    list_display = ("name", "laboratory", "reseller", "city", "status")
    list_filter = ("laboratory", "status")
    search_fields = ("name", "document")
