from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from apps.enterprises.models import Enterprise
from apps.tracking.models import Trip, VehicleGPSPoint
from apps.vehicles.models import Brand, Driver, Vehicle, VehicleDriver


class Command(BaseCommand):

    def handle(self, *args, **options):
        # Создаем группы
        managers_group, created = Group.objects.get_or_create(name="managers")

        if not created:
            return

        vehicles = Vehicle
        content_type = ContentType.objects.get_for_model(vehicles)
        view_vehicle = Permission.objects.get(
            codename="view_vehicle",
            content_type=content_type,
        )
        change_vehicle = Permission.objects.get(
            codename="change_vehicle",
            content_type=content_type,
        )
        delete_vehicle = Permission.objects.get(
            codename="delete_vehicle",
            content_type=content_type,
        )
        add_vehicle = Permission.objects.get(
            codename="add_vehicle",
            content_type=content_type,
        )

        brands = Brand
        content_type = ContentType.objects.get_for_model(brands)
        view_brand = Permission.objects.get(
            codename="view_brand",
            content_type=content_type,
        )

        drivers = Driver
        content_type = ContentType.objects.get_for_model(drivers)
        view_driver = Permission.objects.get(
            codename="view_driver",
            content_type=content_type,
        )
        change_driver = Permission.objects.get(
            codename="change_driver",
            content_type=content_type,
        )
        delete_driver = Permission.objects.get(
            codename="delete_driver",
            content_type=content_type,
        )
        add_driver = Permission.objects.get(
            codename="add_driver",
            content_type=content_type,
        )

        vehicledrivers = VehicleDriver
        content_type = ContentType.objects.get_for_model(vehicledrivers)
        view_vehicledriver = Permission.objects.get(
            codename="view_vehicledriver",
            content_type=content_type,
        )
        change_vehicledriver = Permission.objects.get(
            codename="change_vehicledriver",
            content_type=content_type,
        )
        delete_vehicledriver = Permission.objects.get(
            codename="delete_vehicledriver",
            content_type=content_type,
        )
        add_vehicledriver = Permission.objects.get(
            codename="add_vehicledriver",
            content_type=content_type,
        )

        enterprises = Enterprise
        content_type = ContentType.objects.get_for_model(enterprises)
        view_enterprise = Permission.objects.get(
            codename="view_enterprise",
            content_type=content_type,
        )
        add_enterprise = Permission.objects.get(
            codename="add_enterprise",
            content_type=content_type,
        )

        vehiclegpspoint = VehicleGPSPoint
        content_type = ContentType.objects.get_for_model(vehiclegpspoint)
        view_vehiclegpspoint = Permission.objects.get(
            codename="view_vehiclegpspoint",
            content_type=content_type,
        )
        delete_vehiclegpspoint = Permission.objects.get(
            codename="delete_vehiclegpspoint",
            content_type=content_type,
        )

        trips = Trip
        content_type = ContentType.objects.get_for_model(trips)
        view_trip = Permission.objects.get(
            codename="view_trip",
            content_type=content_type,
        )
        change_trip = Permission.objects.get(
            codename="change_trip",
            content_type=content_type,
        )
        delete_trip = Permission.objects.get(
            codename="delete_trip",
            content_type=content_type,
        )
        add_trip = Permission.objects.get(
            codename="add_trip",
            content_type=content_type,
        )

        # Назначаем разрешения группам
        managers_group.permissions.set(
            [
                view_vehicle,
                change_vehicle,
                delete_vehicle,
                view_brand,
                view_driver,
                change_driver,
                delete_driver,
                view_enterprise,
                view_vehicledriver,
                change_vehicledriver,
                delete_vehicledriver,
                view_vehiclegpspoint,
                delete_vehiclegpspoint,
                view_trip,
                change_trip,
                delete_trip,
                add_vehicledriver,
                add_driver,
                add_trip,
                add_vehicle,
                add_enterprise,
            ]
        )
        print("Группа для менеджеров была создана")
