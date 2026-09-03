from django.contrib import admin

from apps.technicians.models import Technician


@admin.register(Technician)
class TechnicianAdmin(admin.ModelAdmin):
    list_display = ("user", "laboratory", "reseller", "professional_registration", "status")
    list_filter = ("laboratory", "status")
