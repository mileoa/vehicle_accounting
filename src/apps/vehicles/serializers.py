import pytz
from rest_framework import serializers

from .models import Brand, Driver, Vehicle, VehicleDriver


class VehicleSerializer(serializers.ModelSerializer):
    active_driver = serializers.SerializerMethodField()
    purchase_datetime = serializers.SerializerMethodField()

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
            "purchase_datetime",
        )

    def get_active_driver(self, obj):
        active_driver = obj.vehicle_drivers.filter(is_active=True).first()
        if active_driver:
            return active_driver.driver.id
        return None

    def get_purchase_datetime(self, obj):
        purchase_datetime = obj.purchase_datetime
        if purchase_datetime is not None:
            purchase_datetime = purchase_datetime.astimezone(
                pytz.timezone(obj.enterprise.timezone)
            )
        return purchase_datetime


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
