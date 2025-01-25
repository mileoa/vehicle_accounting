from django.contrib import admin
from .models import Vehicle, Brand, Enterprise, Driver, VehicleDriver


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
    ]


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
    ]


class DriverAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "salary",
        "experience_years",
        "enterprise",
    ]


admin.site.register(Vehicle, VehicleAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(Enterprise, EnterpriseAdmin)
admin.site.register(Driver, DriverAdmin)
