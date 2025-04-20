from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from zoneinfo import available_timezones
from django.core.exceptions import ValidationError
from django.contrib.gis.db import models as gis_models
from django.db.models import UniqueConstraint
from django.contrib.auth.models import AbstractUser
import uuid
from . import settings

from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.db.models import Sum
from datetime import datetime, timedelta
from django.utils import timezone
import pytz
import math
import pytz


class CustomUser(AbstractUser):
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="custom_user_set",
        blank=True,
        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_set",
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )


class Brand(models.Model):
    name = models.CharField(max_length=100)
    vehicle_type = models.CharField(
        max_length=50,
        choices=[
            ("noname", "noname"),
            ("sedan", "Легковой"),
            ("truck", "Грузовой"),
            ("bus", "Автобус"),
            ("suv", "Внедорожник"),
        ],
    )

    fuel_tank_capacity_liters = models.PositiveIntegerField(
        help_text="Объем бака л"
    )
    load_capacity_kg = models.PositiveIntegerField(
        help_text="Грузоподъемность кг"
    )
    seats_number = models.PositiveIntegerField(help_text="Количество мест")
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=["id"]),
        ]

    def __str__(self):
        return self.name


class Enterprise(models.Model):
    name = models.CharField(max_length=250, verbose_name="название предприятия")
    city = models.CharField(max_length=250, verbose_name="город")
    phone = models.CharField(max_length=20, verbose_name="телефон")
    email = models.EmailField(verbose_name="email")
    website = models.URLField(blank=True, verbose_name="веб-сайт")
    timezone = models.CharField(
        max_length=50,
        choices=[(tz, tz) for tz in available_timezones()],
        default=settings.TIME_ZONE,
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        indexes = [models.Index(fields=["id"]), models.Index(fields=["uuid"])]

    def __str__(self):
        return self.name


class Manager(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="manager",
        verbose_name="пользователь",
    )
    enterprises = models.ManyToManyField(
        Enterprise, related_name="managers", verbose_name="предприятия"
    )

    class Meta:
        indexes = [
            models.Index(fields=["id"]),
        ]

    def save(self, *args, **kwargs):
        if not self.pk:
            self.user.is_staff = True
            self.user.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username


class Driver(models.Model):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_enterprise = getattr(self, "enterprise", None)

    name = models.CharField(max_length=250, verbose_name="имя")
    salary = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="зарплата"
    )
    experience_years = models.PositiveIntegerField(
        verbose_name="стаж работы (лет)"
    )
    enterprise = models.ForeignKey(
        Enterprise,
        on_delete=models.PROTECT,
        related_name="drivers",
        verbose_name="предприятие",
    )

    class Meta:
        indexes = [
            models.Index(fields=["id"]),
        ]

    def clean(self):
        if not self.pk:
            return None
        if (
            self.__original_enterprise != self.enterprise
            and self.vehicles.exists()
        ):
            raise ValidationError(
                "Водитель не может быть переназначен другому предприятию, если для него назначен автомобиль."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Vehicle(models.Model):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_enterprise = getattr(self, "enterprise", None)

    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="цена"
    )
    year_of_manufacture = models.PositiveIntegerField(
        verbose_name="год выпуска"
    )
    mileage = models.PositiveIntegerField(verbose_name="пробег")
    description = models.TextField(blank=True, verbose_name="описание")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="дата внесения в базу"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="дата обновления в базе"
    )
    car_number = models.CharField(
        max_length=6, verbose_name="номер машины", unique=True
    )
    brand = models.ForeignKey(
        "Brand", on_delete=models.PROTECT, verbose_name="бренд"
    )

    enterprise = models.ForeignKey(
        Enterprise,
        on_delete=models.PROTECT,
        related_name="vehicles",
        verbose_name="предприятие",
    )

    drivers = models.ManyToManyField(
        "Driver",
        through="VehicleDriver",
        related_name="vehicles",
        verbose_name="водители",
    )
    purchase_datetime = models.DateTimeField(
        verbose_name="Время покупки", null=True, blank=True
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        indexes = [models.Index(fields=["id"]), models.Index(fields=["uuid"])]

    def clean(self):
        if not self.pk:
            return None
        if (
            self.__original_enterprise != self.enterprise
            and self.drivers.exists()
        ):
            raise ValidationError(
                "Автомобиль не может быть переназначен другому предприятию, если для него назначен водитель."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.car_number)


class VehicleDriver(models.Model):
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="vehicle_drivers"
    )
    driver = models.ForeignKey(
        Driver, on_delete=models.CASCADE, related_name="driver_vehicles"
    )
    is_active = models.BooleanField(
        default=False, verbose_name="Активный водитель"
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["vehicle", "driver"], name="unique_vehicle_driver"
            ),
            UniqueConstraint(
                fields=["driver", "is_active"],
                condition=models.Q(is_active=True),
                name="unique_active_driver",
                violation_error_message="Данный водитель уже назначен активным для одного из автомобилей.",
            ),
            UniqueConstraint(
                fields=["vehicle", "is_active"],
                condition=models.Q(is_active=True),
                name="unique_active_vehicle",
                violation_error_message="Не может быть назначено больше одного водителя.",
            ),
        ]

    def clean(self):
        if self.vehicle.enterprise != self.driver.enterprise:
            raise ValidationError(
                "Транспортное средство и водитель должны принадлежать одному и тому же предприятию."
            )
        if not self.is_active:
            return None
        if self.vehicle.vehicle_drivers.filter(is_active=True).count() > 1:
            raise ValidationError(
                "Не может быть назначено больше одного водителя."
            )
        if self.driver.driver_vehicles.filter(is_active=True).count() > 1:
            raise ValidationError(
                "Данный водитель уже является активным для другого транспортного средства."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.vehicle.car_number} - {self.driver.name}"


class VehicleGPSPoint(models.Model):
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="gps_points"
    )
    point = gis_models.PointField(verbose_name="Местоположение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время")
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=["vehicle", "created_at"]),
            models.Index(fields=["point"]),
        ]

    def __str__(self):
        return f"({self.point.x}, {self.point.y})"


class VehicleGPSPointArchive(models.Model):
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="archive_gps_points"
    )
    point = gis_models.PointField(verbose_name="Местоположение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время")

    class Meta:
        indexes = [
            models.Index(fields=["vehicle", "created_at"]),
            models.Index(fields=["point"]),
        ]


class Trip(models.Model):

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="trips",
        verbose_name="Автомобиль",
    )
    start_time = models.DateTimeField(verbose_name="Время начала поездки")
    end_time = models.DateTimeField(verbose_name="Время окончания поездки")
    start_point = models.ForeignKey(
        VehicleGPSPoint,
        related_name="trip_starts",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Начальная точка",
    )
    end_point = models.ForeignKey(
        VehicleGPSPoint,
        related_name="trip_ends",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Конечная точка",
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=["vehicle", "start_time", "end_time"]),
            models.Index(fields=["uuid"]),
        ]
        ordering = ["-start_time"]

    def __str__(self):
        return f"Поездка {self.vehicle.car_number}: {self.start_time} - {self.end_time}"

    def clean(self):
        if (
            self.start_time
            and self.end_time
            and self.start_time > self.end_time
        ):
            raise ValidationError(
                "Время начала поездки не может быть позже времени окончания."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def generate_report(self):
        raise NotImplementedError(
            "Subclasses must implement generate_report method"
        )
