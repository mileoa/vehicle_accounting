import random
import time
import math
import requests
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from vehicle_accounting.models import VehicleGPSPoint, Vehicle


class Command(BaseCommand):
    help = "Generate a real-time track for a given vehicle"

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
        while distance_traveled < track_length:
            next_point = generate_next_point(
                current_point, step, center_point, radius
            )
            response = requests.get(
                f"https://graphhopper.com/api/1/route?point={current_point.y},{current_point.x}&point={next_point.y},{next_point.x}&profile=car&locale=en&calc_points=false&vehicle=car&points_encoded=false&key=259eb45a-e4c4-45e0-860e-9b8a44ef1fbb",
                timeout=10,
            )
            route_data = response.json()

            # Extract the route point and calculate the distance traveled
            routed_next_point_coordinates = route_data["paths"][0][
                "snapped_waypoints"
            ]["coordinates"][-1]
            routed_next_point = Point(
                routed_next_point_coordinates[0],
                routed_next_point_coordinates[1],
            )
            distance_traveled += route_data["paths"][0]["distance"] / 1000
            gps_point = VehicleGPSPoint(
                vehicle=vehicle, point=routed_next_point
            )
            gps_point.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Added GPS point[{routed_next_point_coordinates[0]} {routed_next_point_coordinates[1]}] for vehicle {vehicle.car_number} at {datetime.now()}."
                )
            )
            current_point = routed_next_point
            # time.sleep(10)


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
    angle = random.uniform(0.5, 1.5 * 3.14)
    point = Point(
        current_point.x + km_to_rad(step) * math.cos(angle),
        current_point.y + km_to_rad(step) * math.sin(angle),
    )
    while not is_in_radius(center_point, radius, point):
        point = generate_next_point(current_point, step, center_point, radius)
    return point
