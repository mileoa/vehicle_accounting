from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.db.models import UniqueConstraint


class Brand(models.Model):
    name = models.CharField(max_length=100)
    vehicle_type = models.CharField(
        max_length=50,
        choices=[
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

    def __str__(self):
        return self.name


class Enterprise(models.Model):
    name = models.CharField(max_length=250, verbose_name="название предприятия")
    city = models.CharField(max_length=250, verbose_name="город")
    phone = models.CharField(max_length=20, verbose_name="телефон")
    email = models.EmailField(verbose_name="email")
    website = models.URLField(blank=True, verbose_name="веб-сайт")

    def __str__(self):
        return self.name


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
                violation_error_message="Для данного автомобиля уже назначен активный водитель.",
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
                "Для данного транспортного средства уже назначен активный водитель."
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
