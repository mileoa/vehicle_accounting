import math
import random
import time
from datetime import datetime, timedelta, timezone

import requests
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from faker import Faker

from apps.tracking.models import Trip, VehicleGPSPoint
from apps.vehicles.models import Vehicle
from core.settings.local import GRAPHHOPPER_API_KEY


class Command(BaseCommand):
    help = "Generate a real-time track for a given vehicle"
    CONSOLE_PRINT_POINT_CREATED_INTERVAL = 100
    MAX_ATTEMPTS_TO_FIND_POINT = 10

    def add_arguments(self, parser):
        parser.add_argument("vehicle_id", type=int, help="ID of the vehicle")
        parser.add_argument(
            "--center-point",
            type=str,
            default="0.0,0.0",
            help="Center point of the track area (longitude, latitude)",
        )
        parser.add_argument(
            "--radius",
            type=float,
            default=1.0,
            help="Radius of the track area in kilometers",
        )
        parser.add_argument(
            "--length",
            type=float,
            default=10.0,
            help="Length of the track in kilometers",
        )
        parser.add_argument(
            "--step",
            type=float,
            default=0.1,
            help="Step between points in kilometers",
        )

    def handle(self, *args, **options):
        vehicle_id = options["vehicle_id"]
        center_point_str = options["center_point"]
        radius = options["radius"]
        track_length = options["length"]
        step = options["step"]

        try:
            vehicle = Vehicle.objects.get(id=vehicle_id)
        except Vehicle.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f"Vehicle with ID {vehicle_id} does not exist."
                )
            )
            return

        # Get the center point of the track area
        center_point_coords = center_point_str.split(",")
        center_point = Point(
            float(center_point_coords[0]), float(center_point_coords[1])
        )

        # Generate the track
        current_point = get_random_point_in_circle(center_point, radius)

        distance_traveled = 0.0

        start_point = None
        end_point = None

        fake = Faker()
        gps_point_created_at = fake.date_time_between(
            start_date="-25y", end_date="now", tzinfo=timezone.utc
        )
        begin_of_execution_time = datetime.now(timezone.utc)
        attempts_to_find_point = 0
        while (
            distance_traveled < track_length
            and attempts_to_find_point <= self.MAX_ATTEMPTS_TO_FIND_POINT
        ):
            next_point = generate_next_point(
                current_point, step, center_point, radius
            )

            response = requests.get(
                f"https://graphhopper.com/api/1/route?point={current_point.y},{current_point.x}&point={next_point.y},{next_point.x}&profile=car&locale=en&calc_points=true&vehicle=car&points_encoded=false&key={GRAPHHOPPER_API_KEY}",
                timeout=10,
            )

            route_data = response.json()
            if (
                isinstance(route_data["hints"], list)
                and route_data["hints"][0].get("details")
                == "com.graphhopper.util.exceptions.PointNotFoundException"
            ):
                time.sleep(3)
                attempts_to_find_point += 1
                continue
            attempts_to_find_point = 0
            route_points = route_data["paths"][0]["points"]["coordinates"]

            for i, point_coords in enumerate(route_points):
                point = Point(point_coords[0], point_coords[1])

                gps_point = VehicleGPSPoint(vehicle=vehicle, point=point)
                gps_point.save()
                gps_point_created_at = gps_point_created_at + (
                    datetime.now(timezone.utc)
                    - begin_of_execution_time
                    + timedelta(seconds=30)
                )
                gps_point.created_at = gps_point_created_at
                gps_point.save()

                if start_point is None:
                    start_point = gps_point
                end_point = gps_point

                if (
                    i % self.CONSOLE_PRINT_POINT_CREATED_INTERVAL == 0
                    or i == len(route_points) - 1
                ):
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Added GPS point[{point_coords[0]} {point_coords[1]}] ({i+1}/{len(route_points)}) for vehicle {vehicle.car_number} at {datetime.now()}."
                        )
                    )

            current_point = Point(route_points[-1][0], route_points[-1][1])
            distance_traveled += route_data["paths"][0]["distance"] / 1000

            time.sleep(5)

        trip = Trip(
            vehicle=vehicle,
            start_time=start_point.created_at,
            end_time=end_point.created_at,
            start_point=start_point,
            end_point=end_point,
        )
        trip.save()


def get_random_point_in_circle(center_point, radius_km):
    distance = random.uniform(0, 1) * km_to_rad(radius_km)
    angle = random.uniform(0, 2 * math.pi)
    longitude = center_point.x + distance * math.cos(angle)
    latitude = center_point.y + distance * math.sin(angle)

    return Point(longitude, latitude)


def km_to_rad(km):
    return km * 1000 / 60 / 1852


def is_in_radius(center_point, radius, point):
    distance = center_point.distance(point)
    return distance < radius


def generate_next_point(current_point, step, center_point, radius):
    angle = random.uniform(0.0, 2.0 * 3.14)
    point = Point(
        current_point.x + km_to_rad(step) * math.cos(angle),
        current_point.y + km_to_rad(step) * math.sin(angle),
    )
    while not is_in_radius(center_point, radius, point):
        point = generate_next_point(current_point, step, center_point, radius)
    return point
