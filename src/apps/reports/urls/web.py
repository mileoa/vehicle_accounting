from django.urls import path

from apps.reports.views import (
    DriverAssignmentReportView,
    ReportListView,
    VehicleMileageReportView,
    VehicleSalesReportView,
)

app_name = "reports"
urlpatterns = [
    path("", ReportListView.as_view(), name="report_list"),
    path(
        "driver-assignment/",
        DriverAssignmentReportView.as_view(),
        name="report_driver_assignment",
    ),
    path(
        "vehicle-mileage/",
        VehicleMileageReportView.as_view(),
        name="report_vehicle_mileage",
    ),
    path(
        "vehicle-sales/",
        VehicleSalesReportView.as_view(),
        name="report_vehicle_sales",
    ),
]
