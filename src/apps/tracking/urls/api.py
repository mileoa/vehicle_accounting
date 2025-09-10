from rest_framework import routers

from apps.tracking.views import (
    TripGPSPointViewSet,
    TripListViewSet,
    VehicleGPSPointViewSet,
)

app_name = "tracking"
router = routers.DefaultRouter()
router.register(
    r"vehicle_gps_points", VehicleGPSPointViewSet, basename="vehicle_gps_points"
)
router.register(r"trips_tracks", TripGPSPointViewSet, basename="trips_tracks")
router.register(r"trips", TripListViewSet, basename="trips")


urlpatterns = [
    *router.urls,
]
