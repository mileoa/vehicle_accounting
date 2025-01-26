from rest_framework import serializers
from .models import Vehicle, Brand, Driver, Enterprise, VehicleDriver


class VehicleSerializer(serializers.ModelSerializer):
    active_driver = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = (
            "id",
            "price",
            "year_of_manufacture",
            "mileage",
            "description",
            "created_at",
            "updated_at",
            "car_number",
            "brand",
            "enterprise",
            "drivers",
            "active_driver",
        )

    def get_active_driver(self, obj):
        active_driver = obj.vehicle_drivers.filter(is_active=True).first()
        if active_driver:
            return active_driver.driver.id
        return None


class DriverSerializer(serializers.ModelSerializer):

    class Meta:
        model = Driver
        fields = "__all__"


class ActiveVehicleDriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleDriver
        fields = ("vehicle", "driver")


class BrandSerializer(serializers.ModelSerializer):

    class Meta:
        model = Brand
        fields = "__all__"


class EnterpriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enterprise
        fields = "__all__"
