from rest_framework import routers

from apps.enterprises.views import EnterpriseViewSet

app_name = "enterprises"
router = routers.DefaultRouter()
router.register(r"enterprises", EnterpriseViewSet, basename="enterprise")


urlpatterns = [
    *router.urls,
]
