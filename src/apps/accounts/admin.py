from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission

from apps.accounts.models import CustomUser, Manager
from apps.enterprises.models import Enterprise
from apps.tracking.models import Trip
from apps.vehicles.models import Brand, Driver, Vehicle, VehicleDriver


class ManagerAdmin(admin.ModelAdmin):
    list_display = ("user", "get_enterprises")
    filter_horizontal = ("enterprises",)

    def get_enterprises(self, obj):
        return ", ".join(
            [enterpise.name for enterpise in obj.enterprises.all()]
        )

    get_enterprises.short_description = "Предприятия"


admin.site.register(CustomUser, UserAdmin)
admin.site.register(Manager, ManagerAdmin)
