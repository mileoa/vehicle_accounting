from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.db.models import QuerySet
import pytz
from .models import (
    Vehicle,
    Brand,
    Driver,
    Enterprise,
    VehicleDriver,
    VehicleGPSPoint,
    VehicleGPSPointArchive,
    Trip,
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timezone_cache = None

    def get_created_at(self, obj):
        created_at = obj.created_at
        if created_at is None:
            return created_at
        if self.timezone_cache is None:
            self.timezone_cache = pytz.timezone(obj.vehicle.enterprise.timezone)
        created_at = created_at.astimezone(self.timezone_cache)
        return created_at


class VehicleGPSPointArchiveSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = VehicleGPSPointArchive
        fields = ["vehicle", "point", "created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timezone_cache = None

    def get_created_at(self, obj):
        if self.timezone_cache is None:
            self.timezone_cache = pytz.timezone(obj.vehicle.enterprise.timezone)
        created_at = obj.created_at
        if created_at is None:
            return created_at
        created_at = created_at.astimezone(self.timezone_cache)
        return created_at


class GeoJSONVehicleGPSPointSerializer(GeoFeatureModelSerializer):
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = VehicleGPSPoint
        geo_field = "point"
        fields = ["vehicle", "created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timezone_cache = None

    def get_created_at(self, obj):
        if self.timezone_cache is None:
            self.timezone_cache = pytz.timezone(obj.vehicle.enterprise.timezone)
        created_at = obj.created_at
        if created_at is None:
            return created_at
        created_at = created_at.astimezone(self.timezone_cache)
        return created_at


class GeoJSONGPSPointArchiveSerializer(GeoFeatureModelSerializer):
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = VehicleGPSPointArchive
        geo_field = "point"
        fields = ["vehicle", "created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timezone_cache = None

    def get_created_at(self, obj):
        if self.timezone_cache is None:
            self.timezone_cache = pytz.timezone(obj.vehicle.enterprise.timezone)
        created_at = obj.created_at
        if created_at is None:
            return created_at
        created_at = created_at.astimezone(self.timezone_cache)
        return created_at


class TripSerializer(serializers.ModelSerializer):
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = ["id", "vehicle", "start_time", "end_time"]

    def get_start_time(self, obj):
        start_time = obj.start_time
        if start_time is not None:
            start_time = start_time.astimezone(
                pytz.timezone(obj.vehicle.enterprise.timezone)
            )
        return start_time

    def get_end_time(self, obj):
        end_time = obj.end_time
        if end_time is not None:
            end_time = end_time.astimezone(
                pytz.timezone(obj.vehicle.enterprise.timezone)
            )
        return end_time
