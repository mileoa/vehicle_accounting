from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.tracking.models import Trip, VehicleGPSPoint
from apps.tracking.services import get_address_from_coordinates


@receiver(post_save, sender=Trip)
def update_trip_points(sender, instance, **kwargs):

    start_point = (
        VehicleGPSPoint.objects.filter(
            vehicle=instance.vehicle,
            created_at__gte=instance.start_time,
            created_at__lte=instance.end_time,
        )
        .order_by("created_at")
        .first()
    )

    end_point = (
        VehicleGPSPoint.objects.filter(
            vehicle=instance.vehicle,
            created_at__gte=instance.start_time,
            created_at__lte=instance.end_time,
        )
        .order_by("-created_at")
        .first()
    )

    # Обновляем запись Trip, отключая сигнал, чтобы избежать рекурсии
    post_save.disconnect(update_trip_points, sender=Trip)
    instance.start_point = start_point
    instance.end_point = end_point
    instance.save()
    post_save.connect(update_trip_points, sender=Trip)
