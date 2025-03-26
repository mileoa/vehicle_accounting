from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
import pytz
from .models import (
    Vehicle,
    Brand,
    Driver,
    Enterprise,
    VehicleDriver,
    VehicleGPSPoint,
    VehicleGPSPointArchive,
)


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


class EnterpriseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enterprise
        fields = "__all__"


class VehicleGPSPointSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = VehicleGPSPoint
        fields = ["vehicle", "point", "created_at"]

    def get_created_at(self, obj):
        created_at = obj.created_at
        if created_at is not None:
            created_at = created_at.astimezone(
                pytz.timezone(obj.vehicle.enterprise.timezone)
            )
        return created_at


class VehicleGPSPointArchiveSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = VehicleGPSPointArchive
        fields = ["vehicle", "point", "created_at"]

    def get_created_at(self, obj):
        created_at = obj.created_at
        if created_at is not None:
            created_at = created_at.astimezone(
                pytz.timezone(obj.vehicle.enterprise.timezone)
            )
        return created_at


class GeoJSONVehicleGPSPointSerializer(GeoFeatureModelSerializer):
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = VehicleGPSPoint
        geo_field = "point"
        fields = ["vehicle", "created_at"]

    def get_created_at(self, obj):
        created_at = obj.created_at
        if created_at is not None:
            created_at = created_at.astimezone(
                pytz.timezone(obj.vehicle.enterprise.timezone)
            )
        return created_at


class GeoJSONGPSPointArchiveSerializer(GeoFeatureModelSerializer):
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = VehicleGPSPointArchive
        geo_field = "point"
        fields = ["vehicle", "created_at"]

    def get_created_at(self, obj):
        created_at = obj.created_at
        if created_at is not None:
            created_at = created_at.astimezone(
                pytz.timezone(obj.vehicle.enterprise.timezone)
            )
        return created_at
