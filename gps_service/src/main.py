import asyncio
import json
import math
import os
from datetime import datetime

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
last_positions = {}
producer = None
SPEED_LIMIT = 90


class GPSPoint(BaseModel):
    vehicle_id: int
    latitude: float
    longitude: float


def haversine_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Расчет расстояния между двумя GPS точками в километрах
    Формула гаверсинуса
    """
    # Радиус Земли в км
    R = 6371.0

    # Перевод в радианы
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Разности координат
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Формула гаверсинуса
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance


def calculate_speed(
    lat1: float,
    lon1: float,
    time1: datetime,
    lat2: float,
    lon2: float,
    time2: datetime,
) -> float:
    """
    Расчет скорости между двумя GPS точками в км/ч
    """
    # Расстояние в км
    distance_km = haversine_distance(lat1, lon1, lat2, lon2)

    # Время в часах
    time_diff_seconds = (time2 - time1).total_seconds()
    if time_diff_seconds <= 0:
        return 0.0

    time_diff_hours = time_diff_seconds / 3600

    # Скорость км/ч
    speed_kmh = distance_km / time_diff_hours
    return round(speed_kmh, 2)


async def create_producer_with_retry(kafka_servers, max_retries=1000, delay=5):
    for attempt in range(max_retries):
        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=kafka_servers,
                value_serializer=lambda x: json.dumps(x).encode("utf-8"),
            )
            await producer.start()
            print(f"Connected to Kafka on attempt {attempt + 1}")
            return producer
        except (KafkaConnectionError, ConnectionError) as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
            else:
                raise Exception(
                    f"Failed to connect after {max_retries} attempts"
                )


@app.on_event("startup")
async def startup():
    global producer
    kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    producer = await create_producer_with_retry([kafka_servers])


@app.on_event("shutdown")
async def shutdown():
    if producer:
        await producer.stop()


@app.post("/gps")
async def receive_gps(gps_data: GPSPoint):
    vehicle_id = gps_data.vehicle_id
    current_time = datetime.now()

    # Расчет скорости если есть предыдущая точка
    calculated_speed = 0.0
    if vehicle_id in last_positions:
        last_pos = last_positions[vehicle_id]
        calculated_speed = calculate_speed(
            last_pos["latitude"],
            last_pos["longitude"],
            last_pos["timestamp"],
            gps_data.latitude,
            gps_data.longitude,
            current_time,
        )

    # Сообщение для Kafka
    message = {
        "vehicle_id": vehicle_id,
        "latitude": gps_data.latitude,
        "longitude": gps_data.longitude,
        "timestamp": current_time.isoformat(),
        "calculated_speed": calculated_speed,
    }

    await producer.send("gps_points", message)

    alert_sent = False
    if calculated_speed > SPEED_LIMIT:
        alert_message = {
            "vehicle_id": vehicle_id,
            "current_speed": calculated_speed,
            "speed_limit": SPEED_LIMIT,
            "location": {
                "latitude": gps_data.latitude,
                "longitude": gps_data.longitude,
            },
            "timestamp": current_time.isoformat(),
        }
        await producer.send("speed_alerts", alert_message)
        alert_sent = True

    # Обновить последнюю позицию
    last_positions[vehicle_id] = {
        "latitude": gps_data.latitude,
        "longitude": gps_data.longitude,
        "timestamp": current_time,
    }

    return {
        "status": "ok",
        "message": "GPS data sent",
        "alert": alert_sent,
    }


@app.get("/")
async def root():
    return {"message": "GPS Microservice running"}
