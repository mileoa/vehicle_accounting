from django.contrib import admin
from import_export.widgets import ForeignKeyWidget, DecimalWidget
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin, ExportActionMixin
from apps.accounts.models import Manager
from apps.enterprises.models import Enterprise
from .models import Vehicle, Brand, Driver, VehicleDriver


class DotDecimalWidget(DecimalWidget):
    def render(self, value, obj=None):
        if value is None:
            return ""
        return str(value).replace(",", ".")


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

    price = fields.Field(
        column_name="price",
        attribute="price",
        widget=DotDecimalWidget(),
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


admin.site.register(Vehicle, VehicleAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(Driver, DriverAdmin)
