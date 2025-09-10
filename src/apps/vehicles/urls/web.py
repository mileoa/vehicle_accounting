from django.urls import path

from apps.vehicles.views import (
    CreateVehicleView,
    DeleteVehicleView,
    DetailBrandView,
    DetailVehicleView,
    ExportVehicles,
    ImportVehicleView,
    IndexVehicleView,
    UpdateVehicleView,
)

app_name = "vehicles"
urlpatterns = [
    path("", IndexVehicleView.as_view(), name="list"),
    path(
        "<int:pk>/",
        DetailVehicleView.as_view(),
        name="detail",
    ),
    path("create/", CreateVehicleView.as_view(), name="create"),
    path(
        "<int:pk>/update/",
        UpdateVehicleView.as_view(),
        name="update",
    ),
    path(
        "<int:pk>/delete/",
        DeleteVehicleView.as_view(),
        name="delete",
    ),
    path("export/", ExportVehicles.as_view(), name="export"),
    path(
        "import/",
        ImportVehicleView.as_view(),
        name="import",
    ),
    path(
        "brands/<slug:name>/",
        DetailBrandView.as_view(),
        name="brands_detail",
    ),
]
