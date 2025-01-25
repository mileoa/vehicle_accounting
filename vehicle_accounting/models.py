from django.db import models


# Create your models here.
class Vehicle(models.Model):

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
    car_number = models.CharField(max_length=6, verbose_name="Номер машины")
    brand = models.ForeignKey(
        "Brand", on_delete=models.PROTECT, verbose_name="бренд"
    )

    def __str__(self):
        return str(self.id)


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
