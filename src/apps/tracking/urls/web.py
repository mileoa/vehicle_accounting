from django.urls import path

from apps.tracking.views import ExportTrips, ImportTripView, TripMapView

app_name = "tracking"
urlpatterns = [
    path(
        "export/<int:vehicle_id>",
        ExportTrips.as_view(),
        name="trips_export",
    ),
    path(
        "map/",
        TripMapView.as_view(),
        name="trips_map",
    ),
    path(
        "import/<int:vehicle_id>/",
        ImportTripView.as_view(),
        name="trips_import",
    ),
]
