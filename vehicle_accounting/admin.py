from django.contrib import admin
from .models import Vehicle, Brand


# Register your models here.
class VehicleAdmin(admin.ModelAdmin):
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


admin.site.register(Vehicle, VehicleAdmin)
admin.site.register(Brand, BrandAdmin)
