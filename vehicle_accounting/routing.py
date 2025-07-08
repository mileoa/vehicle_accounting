from django.urls import re_path
from .vehicle_status import VehicleStatusConsumer

websocket_urlpatterns = [
    re_path(r"ws/vehicle-status/$", VehicleStatusConsumer.as_asgi()),
]
