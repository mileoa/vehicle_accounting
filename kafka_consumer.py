import json
import os
import django
from kafka import KafkaConsumer
from django.contrib.gis.geos import Point

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vehicle_accounting.settings")
django.setup()

# Импортировать модели после настройки django
from vehicle_accounting.models import Vehicle, VehicleGPSPoint


def main():
    consumer = KafkaConsumer(
        "gps_points",
        bootstrap_servers=["localhost:9092"],
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
    )

    print("Kafka consumer started. Waiting for messages...")

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
