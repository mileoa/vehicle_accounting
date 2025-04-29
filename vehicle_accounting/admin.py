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
    Trip,
)
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission
from zoneinfo import available_timezones
from django.db import models
from django import forms
from rangefilter.filters import (
    DateRangeFilterBuilder,
    DateTimeRangeFilterBuilder,
    NumericRangeFilterBuilder,
    DateRangeQuickSelectListFilterBuilder,
)
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export import resources
from import_export.admin import ImportExportModelAdmin, ExportActionMixin
from .services import get_address_from_coordinates


class ManagerAdmin(admin.ModelAdmin):
    list_display = ("user", "get_enterprises")
    filter_horizontal = ("enterprises",)

    def get_enterprises(self, obj):
        return ", ".join([e.name for e in obj.enterprises.all()])

    get_enterprises.short_description = "Предприятия"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        self.assign_view_permissions(
            obj.user, [Driver, Vehicle, VehicleDriver, Brand, Enterprise, Trip]
        )
        self.assign_add_permissions(
            obj.user, [Driver, Vehicle, VehicleDriver, Enterprise, Trip]
        )
        self.assign_delete_permissions(
            obj.user, [Driver, Vehicle, VehicleDriver]
        )
        self.assign_change_permissions(
            obj.user, [Driver, Vehicle, VehicleDriver, Trip]
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


class VehicleResource(resources.ModelResource):
    uuid = fields.Field(column_name="uuid", attribute="uuid")

    # Используем UUID предприятия вместо его ID
    enterprise_uuid = fields.Field(
        column_name="enterprise_uuid",
        attribute="enterprise",
        widget=ForeignKeyWidget(Enterprise, "uuid"),
    )
    brand_uuid = fields.Field(
        column_name="brand_uuid",
        attribute="brand",
        widget=ForeignKeyWidget(Brand, "uuid"),
    )

    class Meta:
        model = Vehicle
        fields = (
            "uuid",
            "car_number",
            "price",
            "year_of_manufacture",
            "mileage",
            "description",
            "purchase_datetime",
            "enterprise_uuid",
            "brand_uuid",
        )
        export_order = fields


class VehicleAdmin(ImportExportModelAdmin, ExportActionMixin):
    resource_class = VehicleResource
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
    search_fields = ["car_number"]
    list_filter = ["enterprise"]

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


class EnterpriseResource(resources.ModelResource):
    uuid = fields.Field(column_name="uuid", attribute="uuid")

    class Meta:
        model = Enterprise
        fields = (
            "uuid",
            "name",
            "city",
            "phone",
            "email",
            "website",
            "timezone",
        )
        export_order = fields


class EnterpriseAdmin(ImportExportModelAdmin, ExportActionMixin):
    resource_class = EnterpriseResource
    list_display = [
        "id",
        "name",
        "city",
        "phone",
        "email",
        "website",
        "timezone",
    ]
    search_fields = ["name"]

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
    list_display = ["vehicle", "point", "formated_created_at"]
    ordering = ["-created_at"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        manager = Manager.objects.get(user=request.user)
        return qs.filter(vehicle__enterprise__in=manager.enterprises.all())

    def formated_created_at(self, obj):
        if obj.created_at:
            return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return None

    formated_created_at.short_description = "Время"


class VehicleGPSPointArchiveAdmin(admin.ModelAdmin):
    list_display = ["vehicle", "point", "formated_created_at"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        manager = Manager.objects.get(user=request.user)
        return qs.filter(vehicle__enterprise__in=manager.enterprises.all())

    def formated_created_at(self, obj):
        if obj.created_at:
            return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return None

    formated_created_at.short_description = "Время"


class TripResource(resources.ModelResource):
    uuid = fields.Field(column_name="uuid", attribute="uuid")

    vehicle = fields.Field(
        column_name="vehicle_uuid",
        attribute="vehicle",
        widget=ForeignKeyWidget(Vehicle, "uuid"),
    )

    class Meta:
        model = Trip
        fields = (
            "uuid",
            "vehicle",
            "start_time",
            "end_time",
            "start_point",
            "end_point",
        )
        export_order = fields

    def dehydrate_start_point(self, trip):
        if trip.start_point and trip.start_point.point:
            return f"({trip.start_point.point.y}, {trip.start_point.point.x})"
        return None

    def dehydrate_end_point(self, trip):
        if trip.end_point and trip.end_point.point:
            return f"({trip.end_point.point.y}, {trip.end_point.point.x})"
        return None


class TripAdmin(ImportExportModelAdmin, ExportActionMixin):
    resource_class = TripResource
    model = Trip
    list_display = [
        "id",
        "vehicle",
        "formatted_start_point",
        "formatted_end_point",
        "formatted_start_time",
        "formatted_end_time",
    ]
    list_filter = [
        "vehicle__enterprise",
    ]
    search_fields = ["vehicle__car_number"]

    def formatted_start_time(self, obj):
        if obj.start_time:
            return obj.start_time.strftime("%Y-%m-%d %H:%M:%S")
        return None

    def formatted_end_time(self, obj):
        if obj.end_time:
            return obj.end_time.strftime("%Y-%m-%d %H:%M:%S")
        return None

    def formatted_start_point(self, obj):
        if not obj.start_point or not obj.start_point.point:
            return None
        lat, lng = obj.start_point.point.y, obj.start_point.point.x
        start_address = get_address_from_coordinates(lat, lng)["address"]
        return start_address

    def formatted_end_point(self, obj):
        if not obj.end_point or not obj.end_point.point:
            return None
        lat, lng = obj.end_point.point.y, obj.end_point.point.x
        end_address = get_address_from_coordinates(lat, lng)["address"]
        return end_address

    formatted_start_time.short_description = "Время начала поездки"
    formatted_end_time.short_description = "Время окончания поездки"
    formatted_start_point.short_description = "Начальная точка"
    formatted_end_point.short_description = "Конечная точка"

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
admin.site.register(Trip, TripAdmin)
