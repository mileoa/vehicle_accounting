from django.contrib import admin
from django.urls import include, path

from apps.enterprises.views import IndexEnterpisesView

app_name = "vehicle_accounting"

handler403 = "core.views.custom_handler403"
handler401 = "core.views.custom_handler401"

urlpatterns = [
    path("", IndexEnterpisesView.as_view(), name="home"),
    path("admin/", admin.site.urls),
    path(
        "accounts/",
        include("apps.accounts.urls.web", namespace="accounts"),
    ),
    path(
        "enterprises/",
        include("apps.enterprises.urls.web", namespace="enterprises"),
    ),
    path(
        "vehicles/",
        include("apps.vehicles.urls.web", namespace="vehicles"),
    ),
    path(
        "tracking/",
        include("apps.tracking.urls.web", namespace="tracking"),
    ),
    path(
        "reports/",
        include("apps.reports.urls.web", namespace="reports"),
    ),
    path("api/", include("core.urls.api")),
    path("swagger/", include("core.urls.swagger")),
    path("prometheus/", include("django_prometheus.urls")),
]
