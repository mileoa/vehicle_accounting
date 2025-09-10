import json
import os
import sys
import time

import django
from django.contrib.gis.geos import Point
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.local")
django.setup()

from apps.tracking.models import VehicleGPSPoint
from apps.vehicles.models import Vehicle


def create_consumer_with_retry(topic, servers, max_retries=10, delay=5):
    for attempt in range(max_retries):
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=servers,
                value_deserializer=lambda x: json.loads(x.decode("utf-8")),
            )
            print(f"Connected to Kafka on attempt {attempt + 1}")
            return consumer
        except NoBrokersAvailable as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                raise Exception(
                    f"Failed to connect after {max_retries} attempts"
                )


def main():
    consumer = create_consumer_with_retry("gps_points", ["kafka:9092"])

    for message in consumer:
        data = message.value
        print(f"Received GPS data: {data}")

        try:
            # Найти автомобиль
            vehicle = Vehicle.objects.get(id=data["vehicle_id"])

            # Создать GPS точку
            point = Point(data["longitude"], data["latitude"])

            VehicleGPSPoint.objects.create(vehicle=vehicle, point=point)

            print(f"Saved GPS point for vehicle {data['vehicle_id']}")

        except Vehicle.DoesNotExist:
            print(f"Vehicle {data['vehicle_id']} not found")
        except Exception as e:
            print(f"Error saving GPS point: {e}")


if __name__ == "__main__":
    main()
