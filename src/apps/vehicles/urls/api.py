from rest_framework import routers

from apps.vehicles.views import (
    ActiveVehicleDriverViewSet,
    BrandViewSet,
    DriverViewSet,
    VehicleMillageViewSet,
    VehicleViewSet,
)

app_name = "vehicles"
router = routers.DefaultRouter()
router = routers.DefaultRouter()

router.register(r"drivers", DriverViewSet, basename="driver")
router.register(r"brands", BrandViewSet, basename="brand")
router.register(
    r"active_drivers",
    ActiveVehicleDriverViewSet,
    basename="active_driver",
)
router.register(
    "vehicle_mileage_report",
    VehicleMillageViewSet,
    basename="vehicles_mileage_report",
)
router.register(r"vehicles", VehicleViewSet, basename="vehicle")

urlpatterns = [
    *router.urls,
]
