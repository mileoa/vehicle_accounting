from django.contrib import admin
from import_export import fields, resources
from import_export.admin import ExportActionMixin, ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget

from apps.accounts.models import Manager
from apps.tracking.models import Trip, VehicleGPSPoint
from apps.tracking.services import get_address_from_coordinates
from apps.vehicles.models import Vehicle


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


admin.site.register(VehicleGPSPoint, VehicleGPSPointAdmin)
admin.site.register(Trip, TripAdmin)
