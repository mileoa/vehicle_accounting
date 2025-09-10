from django.urls import path

from apps.enterprises.views import (
    ExportEnterprises,
    ImportEnterpriseView,
    IndexEnterpisesView,
)

app_name = "enterprises"
urlpatterns = [
    path("", IndexEnterpisesView.as_view(), name="list"),
    path("import", ImportEnterpriseView.as_view(), name="import"),
    path("export/<int:pk>/", ExportEnterprises.as_view(), name="export"),
]
