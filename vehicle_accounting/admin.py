from django.contrib import admin
from .models import (
    CustomUser,
    Manager,
    Vehicle,
    Brand,
    Enterprise,
    Driver,
    VehicleDriver,
    VehicleGPSPoint,
    VehicleGPSPointArchive,
)
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission
from zoneinfo import available_timezones
from django.db import models
from django import forms


class ManagerAdmin(admin.ModelAdmin):
    list_display = ("user", "get_enterprises")
    filter_horizontal = ("enterprises",)

    def get_enterprises(self, obj):
        return ", ".join([e.name for e in obj.enterprises.all()])

    get_enterprises.short_description = "Предприятия"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        self.assign_view_permissions(
            obj.user, [Driver, Vehicle, VehicleDriver, Brand, Enterprise]
        )
        self.assign_add_permissions(obj.user, [Driver, Vehicle, VehicleDriver])
        self.assign_delete_permissions(
            obj.user, [Driver, Vehicle, VehicleDriver]
        )
        self.assign_change_permissions(
            obj.user, [Driver, Vehicle, VehicleDriver]
        )

    def assign_view_permissions(self, user, models):
        for model in models:
            view_perm = Permission.objects.get(
                content_type__app_label="vehicle_accounting",
                content_type__model=model.__name__.lower(),
                codename=f"view_{model.__name__.lower()}",
            )
            user.user_permissions.add(view_perm)

    def assign_add_permissions(self, user, models):
        for model in models:
            add_perm = Permission.objects.get(
                content_type__app_label="vehicle_accounting",
                content_type__model=model.__name__.lower(),
                codename=f"add_{model.__name__.lower()}",
            )
            user.user_permissions.add(add_perm)

    def assign_delete_permissions(self, user, models):
        for model in models:
            delete_perm = Permission.objects.get(
                content_type__app_label="vehicle_accounting",
                content_type__model=model.__name__.lower(),
                codename=f"delete_{model.__name__.lower()}",
            )
            user.user_permissions.add(delete_perm)

    def assign_change_permissions(self, user, models):
        for model in models:
            change_perm = Permission.objects.get(
                content_type__app_label="vehicle_accounting",
                content_type__model=model.__name__.lower(),
                codename=f"change_{model.__name__.lower()}",
            )
            user.user_permissions.add(change_perm)


class VehicleDriverInline(admin.TabularInline):
    model = VehicleDriver
    extra = 0


class VehicleAdmin(admin.ModelAdmin):
    inlines = [VehicleDriverInline]
    list_display = [
        "id",
        "car_number",
        "brand",
        "price",
        "year_of_manufacture",
        "mileage",
        "created_at",
        "updated_at",
        "description",
        "enterprise",
        "purchase_datetime",
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        manager = Manager.objects.get(user=request.user)
        return qs.filter(enterprise__in=manager.enterprises.all())

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            manager = Manager.objects.get(user=request.user)
            form.base_fields["enterprise"].queryset = manager.enterprises.all()
        return form


class BrandAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "vehicle_type",
        "fuel_tank_capacity_liters",
        "load_capacity_kg",
        "seats_number",
    ]


class EnterpriseAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "city",
        "phone",
        "email",
        "website",
        "timezone",
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        manager = Manager.objects.get(user=request.user)
        return qs.filter(id__in=manager.enterprises.all())


class DriverAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "salary",
        "experience_years",
        "enterprise",
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        manager = Manager.objects.get(user=request.user)
        return qs.filter(enterprise__in=manager.enterprises.all())


class VehicleGPSPointAdmin(admin.ModelAdmin):
    list_display = ["vehicle", "point", "created_at"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        manager = Manager.objects.get(user=request.user)
        return qs.filter(vehicle__enterprise__in=manager.enterprises.all())


class VehicleGPSPointArchiveAdmin(admin.ModelAdmin):
    list_display = ["vehicle", "point", "created_at"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        manager = Manager.objects.get(user=request.user)
        return qs.filter(vehicle__enterprise__in=manager.enterprises.all())


admin.site.register(Vehicle, VehicleAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(Enterprise, EnterpriseAdmin)
admin.site.register(Driver, DriverAdmin)
admin.site.register(CustomUser, UserAdmin)
admin.site.register(Manager, ManagerAdmin)
admin.site.register(VehicleGPSPoint, VehicleGPSPointAdmin)
admin.site.register(VehicleGPSPointArchive, VehicleGPSPointArchiveAdmin)
