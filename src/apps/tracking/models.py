import uuid

from django.contrib.gis.db import models as gis_models
from django.core.exceptions import ValidationError
from django.db import models

from apps.vehicles.models import Vehicle


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

    class Meta:
        indexes = [
            models.Index(fields=["vehicle", "start_time", "end_time"]),
            models.Index(fields=["uuid"]),
        ]
        ordering = ["-start_time"]

    def __str__(self):
        return f"Поездка {self.vehicle.car_number}: {self.start_time} - {self.end_time}"
