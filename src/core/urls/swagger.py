from django.urls import path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Vehicle accounting",
        default_version="v1",
        description="Спецификация для проекта vehicle accounting",
        terms_of_service="https://www.test./",
        contact=openapi.Contact(email="test@test.test"),
        license=openapi.License(name="test"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


app_name = "vehicle_accounting"
urlpatterns = [
    path(
        "",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    re_path(
        r"^(?P<format>json|yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
]
