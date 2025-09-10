from django.urls import include, path

urlpatterns = [
    path(
        "accounts/",
        include("apps.accounts.urls.api", namespace="accounts_api"),
    ),
    path(
        "vehicles/",
        include("apps.vehicles.urls.api", namespace="vehicles_api"),
    ),
    path(
        "enterprises/",
        include("apps.enterprises.urls.api", namespace="enterprises_api"),
    ),
    path(
        "tracking/",
        include("apps.tracking.urls.api", namespace="tracking_api"),
    ),
]
