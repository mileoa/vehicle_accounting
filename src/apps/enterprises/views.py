import uuid

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.views.generic import ListView, View
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.renderers import JSONRenderer

from apps.accounts.models import Manager
from apps.importer_exporter.views import ImportView
from core.permissions import HasRoleOrSuper

from .admin import EnterpriseResource
from .mixins import WebEnterpriseMixin
from .models import Enterprise
from .serializers import EnterpriseSerializer


class EnterpriseViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    serializer_class = EnterpriseSerializer
    pagination_class = PageNumberPagination
    ordering_fields = ["id"]
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 100
    permission_classes = [
        IsAuthenticated,
        HasRoleOrSuper("manager"),
        DjangoModelPermissions,
    ]
    paginate_by = 25

    @method_decorator(cache_page(60 * 60 * 2))
    @method_decorator(vary_on_cookie)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Enterprise.objects.all().order_by("id")
        manager = Manager.objects.get(user=self.request.user)
        return Enterprise.objects.filter(
            id__in=manager.enterprises.all()
        ).order_by("id")

    def get_all(self):
        return Enterprise.objects.all().order_by("id")

    def get_object(self):
        obj = get_object_or_404(self.get_all(), pk=self.kwargs["pk"])
        if obj not in self.get_queryset():
            raise PermissionDenied(
                detail="You do not have permission to access this object."
            )
        return obj


class IndexEnterpisesView(WebEnterpriseMixin, ListView):
    http_method_names = ["get"]
    context_object_name = "enterprises"
    template_name = "enterprises/enterprise_list.html"
    paginate_by = 100
    ordering = ["id"]
    permission_required = ["enterprises.view_enterprise"]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Enterprise.objects.all()
        manager = Manager.objects.get(user=self.request.user)
        return Enterprise.objects.filter(id__in=manager.enterprises.all())


class ExportEnterprises(WebEnterpriseMixin, View):
    model = Enterprise
    permission_required = [
        "enterprises.view_enterprise",
    ]

    def get(self, request, *args, **kwargs):
        export_format = request.GET.get("export_format", "csv")
        dataset = EnterpriseResource().export(self.get_queryset())
        if export_format == "json":
            response = HttpResponse(dataset.json, content_type="json")
            response["Content-Disposition"] = (
                "attachment; filename=enterprises.json"
            )
        else:
            response = HttpResponse(dataset.csv, content_type="csv")
            response["Content-Disposition"] = (
                "attachment; filename=enterprises.csv"
            )

        return response

    def get_queryset(self):
        queryset = Enterprise.objects.filter(id=self.kwargs["pk"])
        if self.request.user.is_superuser:
            return queryset
        manager = Manager.objects.get(user=self.request.user)
        queryset = queryset.filter(id__in=manager.enterprises.all())
        return queryset


class ImportEnterpriseView(WebEnterpriseMixin, ImportView):
    template_name = "enterprises/enterprise_import.html"
    success_url = reverse_lazy("enterprises_list")
    permission_required = ["enterprises.add_enterprise"]

    def process_data(self, data, update_existing, request):
        created_count = 0
        updated_count = 0
        error_count = 0
        errors = []

        for row in data:
            try:
                # Обязательные поля
                name = row.get("name")
                city = row.get("city")
                phone = row.get("phone")
                email = row.get("email")

                # Необязательные поля
                enterprise_uuid = row.get("uuid")
                website = row.get("website", "")
                timezone_str = row.get("timezone", "UTC")

                # Проверка обязательных полей
                if not all([name, city, phone, email]):
                    error_count += 1
                    errors.append(
                        f"Отсутствуют обязательные поля для предприятия: {row}"
                    )
                    continue

                # Проверка существования предприятия
                exists = False
                if enterprise_uuid:
                    exists = Enterprise.objects.filter(
                        uuid=enterprise_uuid
                    ).exists()

                if exists and update_existing:
                    enterprise = Enterprise.objects.get(uuid=enterprise_uuid)
                    enterprise.name = name
                    enterprise.city = city
                    enterprise.phone = phone
                    enterprise.email = email
                    enterprise.website = website
                    enterprise.timezone = timezone_str
                    enterprise.save()
                    updated_count += 1
                elif not exists:
                    new_enterprise_uuid = uuid.uuid4()
                    Enterprise.objects.create(
                        uuid=new_enterprise_uuid,
                        name=name,
                        city=city,
                        phone=phone,
                        email=email,
                        website=website,
                        timezone=timezone_str,
                    )
                    created_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"Ошибка при обработке строки {row}: {str(e)}")

        result = {
            "success": error_count == 0,
            "message": "",
            "created_count": created_count,
            "updated_count": updated_count,
            "error_count": error_count,
        }

        if errors:
            result["message"] += "\n\nОшибки:\n" + "\n".join(errors)

        return result
