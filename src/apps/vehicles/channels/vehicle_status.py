import asyncio
import json
from datetime import datetime, timedelta

import rx
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from rx import operators as ops
from rx.subject import BehaviorSubject

from apps.tracking.models import VehicleGPSPoint
from apps.vehicles.models import Vehicle


class VehicleStatusTracker:

    def __init__(self):
        self.vehicle_statuses = BehaviorSubject({})
        self.channel_layer = get_channel_layer()
        self.update_trigger = rx.interval(15)

        self._setup_status_pipeline()

    def _setup_status_pipeline(self):
        """Настройка pipeline статусов"""

        self.update_trigger.pipe(
            # Получение статусов всех автомобилей
            ops.map(lambda _: self._calculate_all_statuses()),
            # Сравнение с предыдущими статусами
            ops.scan(self._detect_status_changes, {}),
            # Фильтрация только изменений
            ops.filter(lambda changes: len(changes["changed"]) > 0),
            # Обработка ошибок
            ops.catch(self._handle_error),
        ).subscribe(
            on_next=self._broadcast_status_changes,
            on_error=lambda e: print(f"Status tracker error: {e}"),
        )

    def _handle_error(self, error, source):
        print(f"Pipeline error: {error}")
        return source

    def _calculate_all_statuses(self):
        """Расчет статусов всех автомобилей"""
        statuses = {}
        now = datetime.now()

        latest_gps_points = (
            VehicleGPSPoint.objects.select_related("vehicle")
            .filter(vehicle__in=Vehicle.objects.all())
            .order_by("vehicle", "-created_at")
            .distinct("vehicle")
        )

        latest_gps_dict = {gps.vehicle_id: gps for gps in latest_gps_points}

        vehicles = Vehicle.objects.all()
        for vehicle in vehicles:
            latest_gps = latest_gps_dict.get(vehicle.id)
            status_info = self._determine_vehicle_status(
                vehicle, latest_gps, now
            )
            statuses[vehicle.id] = status_info

        print(statuses)
        return statuses

    def _determine_vehicle_status(self, vehicle, latest_gps, current_time):
        """Определение статуса автомобиля"""
        if not latest_gps:
            return {
                "vehicle_id": vehicle.id,
                "status": "no_data",
                "color": "#6c757d",
                "text": "Нет данных",
                "last_seen": None,
                "minutes_ago": None,
            }

        time_diff = (
            current_time - latest_gps.created_at.replace(tzinfo=None)
        ).total_seconds()
        minutes_ago = int(time_diff / 60)

        # Определение статуса по времени последней активности
        if time_diff <= 300:  # 5 минут
            status = "online"
            color = "#22c55e"
            text = "В сети"
        elif time_diff <= 1800:  # 30 минут
            status = "idle"
            color = "#f59e0b"
            text = "Ожидание"
        elif time_diff <= 7200:  # 2 часа
            status = "inactive"
            color = "#fd7e14"
            text = "Неактивен"
        else:
            status = "offline"
            color = "#dc3545"
            text = "Не в сети"

        return {
            "vehicle_id": vehicle.id,
            "status": status,
            "color": color,
            "text": text,
            "last_seen": latest_gps.created_at.isoformat(),
            "minutes_ago": minutes_ago,
        }

    def _detect_status_changes(self, previous_statuses, current_statuses):
        """Обнаружение изменений статусов"""
        changed = []
        unchanged = []

        for vehicle_id, current_status in current_statuses.items():
            previous_status = previous_statuses.get(vehicle_id)

            if (
                not previous_status
                or previous_status["status"] != current_status["status"]
            ):
                changed.append(
                    {
                        "vehicle_id": vehicle_id,
                        "old_status": (
                            previous_status["status"]
                            if previous_status
                            else None
                        ),
                        "new_status": current_status["status"],
                        "status_info": current_status,
                    }
                )
            else:
                unchanged.append(vehicle_id)

        return {
            "changed": changed,
            "unchanged": unchanged,
            "all_statuses": current_statuses,
            "timestamp": datetime.now().isoformat(),
        }

    def _broadcast_status_changes(self, changes):
        """Отправка изменений статусов"""
        if "error" in changes:
            return

        # Обновляем BehaviorSubject
        self.vehicle_statuses.on_next(changes["all_statuses"])

        # WebSocket уведомления
        for change in changes["changed"]:
            async_to_sync(self.channel_layer.group_send)(
                "vehicle_status",
                {
                    "type": "status_change",
                    "vehicle_id": change["vehicle_id"],
                    "status_info": change["status_info"],
                    "old_status": change["old_status"],
                },
            )

        print(f"Status changes broadcast: {len(changes['changed'])} vehicles")

    def get_vehicle_status(self, vehicle_id):
        """Получение статуса конкретного автомобиля"""
        all_statuses = self.vehicle_statuses.value
        return all_statuses.get(vehicle_id)

    def get_all_statuses(self):
        """Получение всех статусов"""
        return self.vehicle_statuses.value

    def subscribe_to_changes(self, callback):
        """Подписка на изменения статусов"""
        return self.vehicle_statuses.subscribe(callback)


# WebSocket Consumer
class VehicleStatusConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status_tracker = VehicleStatusTracker()

    async def connect(self):
        await self.channel_layer.group_add("vehicle_status", self.channel_name)
        await self.accept()
        asyncio.create_task(self.send_ping())

    async def send_ping(self):
        while True:
            try:
                await asyncio.sleep(30)
                await self.send(text_data='{"type": "ping"}')
            except:
                break

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "vehicle_status", self.channel_name
        )

    async def status_change(self, event):
        """Обработка изменения статуса"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "status_update",
                    "vehicle_id": event["vehicle_id"],
                    "status_info": event["status_info"],
                    "old_status": event["old_status"],
                }
            )
        )
