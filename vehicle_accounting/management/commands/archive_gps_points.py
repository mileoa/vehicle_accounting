from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from vehicle_accounting.models import VehicleGPSPoint, VehicleGPSPointArchive
from vehicle_accounting.settings import DAYS_TO_MOVE_VEHICLE_GPS_TO_ARCHIVE


class Command(BaseCommand):
    help = "Archive old GPS points"

    def handle(self, *args, **options):
        days = DAYS_TO_MOVE_VEHICLE_GPS_TO_ARCHIVE
        cutoff_date = timezone.now() - timedelta(days=days)

        # Fetch GPS points older than the cutoff date
        old_points = VehicleGPSPoint.objects.filter(created_at__lt=cutoff_date)

        # Create new records in the archive table
        archive_points = [
            VehicleGPSPointArchive(
                vehicle=point.vehicle,
                point=point.point,
                created_at=point.created_at,
            )
            for point in old_points
        ]
        VehicleGPSPointArchive.objects.bulk_create(archive_points)

        # Delete old points from the main table
        old_points.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Archived {len(archive_points)} GPS points older than {days} days."
            )
        )
