"""
URL configuration for vehicle_accounting project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    CustomLoginView,
    VehicleViewSet,
    BrandViewSet,
    DriverViewSet,
    EnterpriseViewSet,
    ActiveVehicleDriverViewSet,
    IndexVehicleView,
    CreateVehicleView,
    UpdateVehicleView,
    DeleteVehicleView,
    IndexEnterpisesView,
    IndexEnterpiseVehiclesView,
    VehicleGPSPointViewSet,
)

handler403 = "vehicle_accounting.views.custom_handler403"
handler401 = "vehicle_accounting.views.custom_handler401"

router = DefaultRouter()
router.register(r"vehicles", VehicleViewSet, basename="vehicles")
router.register(r"brands", BrandViewSet, basename="brands")
router.register(r"drivers", DriverViewSet, basename="drivers")
router.register(r"enterprises", EnterpriseViewSet, basename="enterprises")
router.register(
    r"active_drivers",
    ActiveVehicleDriverViewSet,
    basename="active_drivers",
)
router.register(
    r"vehicle_gps_points", VehicleGPSPointViewSet, basename="vehicle_gps_points"
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("vehicles/", IndexVehicleView.as_view(), name="vehicles_list"),
    path(
        "vehicles/create/", CreateVehicleView.as_view(), name="vehicles_create"
    ),
    path(
        "vehicles/<int:pk>/update/",
        UpdateVehicleView.as_view(),
        name="vehicles_update",
    ),
    path(
        "vehicles/<int:pk>/delete/",
        DeleteVehicleView.as_view(),
        name="vehicles_delete",
    ),
    path(
        "enterprises/",
        IndexEnterpisesView.as_view(),
        name="enterprises_list",
    ),
    path(
        "enterprises/<int:pk>/vehicles/",
        IndexEnterpiseVehiclesView.as_view(),
        name="enterprise_vehicles_list",
    ),
    path(
        "enterprises/<int:pk>/vehicles/",
        IndexEnterpiseVehiclesView.as_view(),
        name="enterprise_vehicles_list",
    ),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path(
        "api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"
    ),
    path("api/", include(router.urls)),
]
