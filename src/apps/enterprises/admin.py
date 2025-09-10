from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin, ExportActionMixin
from apps.accounts.models import Manager
from .models import Enterprise


class EnterpriseResource(resources.ModelResource):
    uuid = fields.Field(column_name="uuid", attribute="uuid")

    class Meta:
        model = Enterprise
        fields = (
            "uuid",
            "name",
            "city",
            "phone",
            "email",
            "website",
            "timezone",
        )
        export_order = fields


class EnterpriseAdmin(ImportExportModelAdmin, ExportActionMixin):
    resource_class = EnterpriseResource
    list_display = [
        "id",
        "name",
        "city",
        "phone",
        "email",
        "website",
        "timezone",
    ]
    search_fields = ["name"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        manager = Manager.objects.get(user=request.user)
        return qs.filter(id__in=manager.enterprises.all())


admin.site.register(Enterprise, EnterpriseAdmin)
