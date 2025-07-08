import rx
from rx import operators as ops
from rx.subject import BehaviorSubject
from datetime import datetime, timedelta
from vehicle_accounting.models import Vehicle, VehicleGPSPoint
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
import json


class VehicleStatusTracker:

    def __init__(self):
        self.vehicle_statuses = BehaviorSubject({})
        self.channel_layer = get_channel_layer()
        self.update_trigger = rx.interval(15)  # обновление каждые 15 сек

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
            ops.catch(
                lambda error, source: rx.just(
                    {
                        "error": str(error),
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            ),
        ).subscribe(
            on_next=self._broadcast_status_changes,
            on_error=lambda e: print(f"Status tracker error: {e}"),
        )

    def _calculate_all_statuses(self):
        """Расчет статусов всех автомобилей"""
        statuses = {}
        now = datetime.now()

        vehicles = Vehicle.objects.all()

        for vehicle in vehicles:
            # Последняя GPS точка
            latest_gps = (
                VehicleGPSPoint.objects.filter(vehicle=vehicle)
                .order_by("-created_at")
                .first()
            )

            status_info = self._determine_vehicle_status(
                vehicle, latest_gps, now
            )
            statuses[vehicle.id] = status_info

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


# Глобальный экземпляр
status_tracker = VehicleStatusTracker()


# WebSocket Consumer
class VehicleStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("vehicle_status", self.channel_name)
        await self.accept()

        # Отправляем текущие статусы при подключении
        current_statuses = status_tracker.get_all_statuses()
        await self.send(
            text_data=json.dumps(
                {"type": "initial_statuses", "statuses": current_statuses}
            )
        )

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
