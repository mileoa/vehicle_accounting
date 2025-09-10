from datetime import datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.core.cache import cache
from django.db.models import ProtectedError
from django.http import HttpResponse
from django.shortcuts import HttpResponseRedirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    View,
)
from rest_framework import serializers as rest_serializers
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from apps.accounts.models import Manager
from apps.enterprises.models import Enterprise
from apps.importer_exporter.views import ImportView
from apps.reports.services import VehicleMileageReport
from core.permissions import HasRoleOrSuper

from .admin import VehicleResource
from .forms import VehicleForm
from .mixins import WebBrandMixin, WebVehicleMixin
from .models import Brand, Driver, Vehicle, VehicleDriver
from .serializers import (
    ActiveVehicleDriverSerializer,
    BrandSerializer,
    DriverSerializer,
    VehicleSerializer,
)


class IndexVehicleView(
    WebVehicleMixin,
    ListView,
):
    http_method_names = ["get"]
    context_object_name = "vehicles"
    template_name = "vehicles/vehicle_list.html"
    paginate_by = 100
    permission_required = ["vehicles.view_vehicle"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enterprise_id = self.request.GET.get("enterprise_id", None)
        if enterprise_id is not None:
            context["enterprise_name"] = Enterprise.objects.get(
                pk=enterprise_id
            ).name
        else:
            context["enterprise_name"] = None
        return context

    def get_queryset(self):
        queryset = Vehicle.objects.all()
        requested_enterprise_id = self.request.GET.get("enterprise_id", None)
        if requested_enterprise_id is not None:

            queryset = queryset.filter(enterprise=requested_enterprise_id)

        if self.request.user.is_superuser:
            return queryset

        if (
            hasattr(self.request.user, "manager")
            and requested_enterprise_id is None
        ):
            enterprise_ids = self.request.user.manager.enterprises.values_list(
                "id", flat=True
            )
            return queryset.filter(enterprise_id__in=enterprise_ids)

        if (
            hasattr(self.request.user, "manager")
            and requested_enterprise_id is not None
        ):
            return queryset

        return Vehicle.objects.none()

    def has_permission(self):
        if self.request.user.is_superuser:
            return True
        requested_enterprise_id = self.request.GET.get("enterprise_id", None)
        if (
            hasattr(self.request.user, "manager")
            and requested_enterprise_id is None
        ):
            return True
        if hasattr(self.request.user, "manager"):
            manager = self.request.user.manager
            return manager.enterprises.filter(
                pk=requested_enterprise_id
            ).exists()
        return False


class CreateVehicleView(WebVehicleMixin, CreateView):

    http_method_names = ["get", "post"]
    template_name = "vehicles/vehicle_create.html"
    success_url = reverse_lazy("vehicles:list")
    permission_required = ["vehicles.add_vehicle"]
    form_class = VehicleForm
    success_message = "Машина успешно создана"

    def get_initial(self):
        initial = super().get_initial()
        request_enterprise_id = self.request.GET.get("enterprise_id")
        if (
            request_enterprise_id is not None
            and Enterprise.objects.filter(pk=request_enterprise_id).exists()
        ):
            initial["enterprise"] = Enterprise.objects.get(
                pk=request_enterprise_id
            )
        else:
            initial["enterprise"] = Enterprise.objects.get(name="noname")
        initial["brand"] = Brand.objects.get(name="noname")
        return initial

    def form_valid(self, form):
        if self.request.user.is_superuser:
            return super().form_valid(form)
        manager = self.request.user.manager
        if form.cleaned_data["enterprise"] not in manager.enterprises.all():
            form.add_error(
                "enterprise",
                "Вы можете использовать только те предприятия, которые назначены вам",
            )
            return self.form_invalid(form)
        return super().form_valid(form)


class UpdateVehicleView(WebVehicleMixin, UpdateView):

    http_method_names = ["get", "post"]
    template_name = "vehicles/vehicle_update.html"
    success_url = reverse_lazy("vehicles:list")
    permission_required = [
        "vehicles.change_vehicle",
    ]
    form_class = VehicleForm
    context_object_name = "vehicle"
    success_message = "Машина успешно изменена"

    def form_valid(self, form):
        if self.request.user.is_superuser:
            return super().form_valid(form)
        manager = self.request.user.manager
        if form.cleaned_data["enterprise"] not in manager.enterprises.all():
            form.add_error(
                "enterprise",
                "Вы можете использовать только те предприятия, которые назначены вам",
            )
            return self.form_invalid(form)
        return super().form_valid(form)

    def has_permission(self):
        if self.request.user.is_superuser:
            return True
        if hasattr(self.request.user, "manager"):
            vehicle = self.get_object()
            manager = self.request.user.manager
            return vehicle.enterprise in manager.enterprises.all()
        return False


class DeleteVehicleView(WebVehicleMixin, DeleteView):

    http_method_names = ["get", "post"]
    template_name = "vehicles/vehicle_delete.html"
    permission_required = ["vehicles.change_vehicle"]
    context_object_name = "vehicle"
    success_url = reverse_lazy("vehicles:list")

    def has_permission(self):
        if self.request.user.is_superuser:
            return True
        if hasattr(self.request.user, "manager"):
            vehicle = self.get_object()
            manager = self.request.user.manager
            return vehicle.enterprise in manager.enterprises.all()
        return False

    def post(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            success_url = self.get_success_url()
            self.object.delete()
            messages.add_message(
                request, messages.SUCCESS, "Машина успешно удалена"
            )
            return HttpResponseRedirect(success_url)
        except ProtectedError:
            messages.add_message(
                request,
                messages.ERROR,
                "Невозможно удалить машину, так как она связаны с другим объектами",
            )
            return HttpResponseRedirect(reverse_lazy("status_list"))


class DetailVehicleView(WebVehicleMixin, DetailView):

    http_method_names = ["get"]
    template_name = "vehicles/vehicle_detail.html"
    permission_required = ["vehicles.view_vehicle"]
    context_object_name = "vehicle"

    def has_permission(self):
        if self.request.user.is_superuser:
            return True
        if hasattr(self.request.user, "manager"):
            vehicle = self.get_object()
            manager = self.request.user.manager
            return vehicle.enterprise in manager.enterprises.all()
        return False


class VehicleViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    serializer_class = VehicleSerializer
    pagination_class = PageNumberPagination
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 100
    filter_backends = [OrderingFilter]
    ordering_fields = ["id", "price", "created_at"]
    permission_classes = [
        IsAuthenticated,
        HasRoleOrSuper("managers"),
        DjangoModelPermissions,
    ]

    @method_decorator(cache_page(60 * 60 * 2))
    @method_decorator(vary_on_cookie)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Vehicle.objects.all()
        manager = Manager.objects.get(user=self.request.user)
        return Vehicle.objects.filter(enterprise__in=manager.enterprises.all())

    def get_all(self):
        return Vehicle.objects.all()

    def get_object(self):
        obj = get_object_or_404(self.get_all(), pk=self.kwargs["pk"])
        if obj not in self.get_queryset():
            raise PermissionDenied(
                detail="You do not have permission to access this object."
            )
        return obj


class ExportVehicles(LoginRequiredMixin, PermissionRequiredMixin, View):
    model = Vehicle
    permission_required = [
        "vehicles.view_vehicle",
    ]

    def get(self, request, *args, **kwargs):
        export_format = request.GET.get("export_format", "csv")
        dataset = VehicleResource().export(self.get_queryset())
        if export_format == "json":
            response = HttpResponse(dataset.json, content_type="json")
            response["Content-Disposition"] = (
                "attachment; filename=vehicles.json"
            )
        else:
            response = HttpResponse(dataset.csv, content_type="csv")
            response["Content-Disposition"] = (
                "attachment; filename=vehicles.csv"
            )

        return response

    def get_queryset(self):
        queryset = Vehicle.objects.all()

        enterprise_id = self.request.GET.get("enterprise_id")
        if enterprise_id is not None:
            queryset = queryset.filter(enterprise__id=enterprise_id)

        vehicle_id = self.request.GET.get("vehicle_id")
        if vehicle_id is not None:
            queryset = queryset.filter(id=vehicle_id)

        if self.request.user.is_superuser:
            return queryset
        manager = Manager.objects.get(user=self.request.user)
        queryset = queryset.filter(enterprise__in=manager.enterprises.all())
        return queryset


class BrandViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    pagination_class = PageNumberPagination
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 100
    permission_classes = [
        IsAuthenticated,
        HasRoleOrSuper("managers"),
        DjangoModelPermissions,
    ]
    paginate_by = 25

    @method_decorator(cache_page(60 * 60 * 2))
    @method_decorator(vary_on_cookie)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class DriverViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    serializer_class = DriverSerializer
    pagination_class = PageNumberPagination
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 100
    permission_classes = [
        IsAuthenticated,
        HasRoleOrSuper("managers"),
        DjangoModelPermissions,
    ]
    paginate_by = 25

    @method_decorator(cache_page(60 * 60 * 2))
    @method_decorator(vary_on_cookie)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Driver.objects.all()
        manager = Manager.objects.get(user=self.request.user)
        return Driver.objects.filter(enterprise__in=manager.enterprises.all())

    def get_all(self):
        return Vehicle.objects.all()

    def get_object(self):
        obj = get_object_or_404(self.get_all(), pk=self.kwargs["pk"])
        if obj not in self.get_queryset():
            raise PermissionDenied(
                detail="You do not have permission to access this object."
            )
        return obj


class ActiveVehicleDriverViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    serializer_class = ActiveVehicleDriverSerializer
    pagination_class = PageNumberPagination
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 100
    permission_classes = [
        IsAuthenticated,
        HasRoleOrSuper("managers"),
        DjangoModelPermissions,
    ]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return VehicleDriver.objects.all()
        manager = Manager.objects.get(user=self.request.user)
        return VehicleDriver.objects.filter(
            vehicle__enterprise__in=manager.enterprises.all(), is_active=True
        )

    def get_all(self):
        return Vehicle.objects.all()

    def get_object(self):
        obj = get_object_or_404(self.get_all(), pk=self.kwargs["pk"])
        if obj not in self.get_queryset():
            raise PermissionDenied(
                detail="You do not have permission to access this object."
            )
        return obj


class ImportVehicleView(ImportView):
    template_name = "vehicles/vehicle_import.html"
    success_url = reverse_lazy("vehicles:list")
    permission_required = ["vehicles.add_vehicle"]

    def process_data(self, data, update_existing, request):
        created_count = 0
        updated_count = 0
        error_count = 0
        errors = []

        # Получаем список предприятий пользователя, если он не суперпользователь
        if not request.user.is_superuser:
            manager = Manager.objects.get(user=request.user)
            allowed_enterprises = set(
                manager.enterprises.values_list("id", flat=True)
            )

        for row in data:
            try:
                # Обязательные поля
                car_uuid = row.get("uuid")
                car_number = row.get("car_number")
                price = row.get("price")
                year_of_manufacture = row.get("year_of_manufacture")
                mileage = row.get("mileage")
                brand_uuid = row.get("brand_uuid")
                enterprise_uuid = row.get("enterprise_uuid")

                # Необязательные поля
                description = row.get("description", "")
                purchase_datetime_str = row.get("purchase_datetime")
                purchase_datetime = None

                if purchase_datetime_str:
                    purchase_datetime = datetime.fromisoformat(
                        purchase_datetime_str.replace("Z", "+00:00")
                    )

                # Проверка обязательных полей
                if not all(
                    [
                        car_uuid,
                        car_number,
                        price,
                        year_of_manufacture,
                        mileage,
                        brand_uuid,
                        enterprise_uuid,
                    ]
                ):
                    error_count += 1
                    errors.append(
                        f"Отсутствуют обязательные поля для машины: {row}"
                    )
                    continue

                try:
                    enterprise = Enterprise.objects.get(uuid=enterprise_uuid)
                except Enterprise.DoesNotExist:
                    error_count += 1
                    errors.append(f"Предприятие '{enterprise_uuid}' не найдено")
                    continue

                # Проверяем права доступа к предприятию
                if (
                    not request.user.is_superuser
                    and enterprise.id not in allowed_enterprises
                ):
                    error_count += 1
                    errors.append(
                        f"У вас нет прав на добавление машин для предприятия: {enterprise.name}"
                    )
                    continue

                # Получаем бренд
                try:
                    brand = Brand.objects.get(uuid=brand_uuid)
                except Brand.DoesNotExist:
                    error_count += 1
                    errors.append(
                        f"Бренд '{brand_uuid}' не найден для машины: {car_number}"
                    )
                    continue

                # Проверка существования машины
                exists = Vehicle.objects.filter(uuid=car_uuid).exists()

                if exists and update_existing:
                    vehicle = Vehicle.objects.get(uuid=car_uuid)
                    vehicle.car_number = car_number
                    vehicle.price = Decimal(price)
                    vehicle.year_of_manufacture = int(year_of_manufacture)
                    vehicle.mileage = int(mileage)
                    vehicle.description = description
                    vehicle.brand = brand
                    vehicle.enterprise = enterprise
                    if purchase_datetime:
                        vehicle.purchase_datetime = purchase_datetime
                    vehicle.save()
                    updated_count += 1
                elif not exists:
                    Vehicle.objects.create(
                        uuid=car_uuid,
                        car_number=car_number,
                        price=Decimal(price),
                        year_of_manufacture=int(year_of_manufacture),
                        mileage=int(mileage),
                        description=description,
                        brand=brand,
                        enterprise=enterprise,
                        purchase_datetime=purchase_datetime,
                    )
                    created_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"Ошибка при обработке строки {row}: {str(e)}")

        result = {
            "success": error_count == 0,
            "message": f"Импорт завершен. Создано: {created_count}, Обновлено: {updated_count}, Ошибок: {error_count}",
            "created_count": created_count,
            "updated_count": updated_count,
            "error_count": error_count,
        }

        if errors:
            result["message"] += "\n\nОшибки:\n" + "\n".join(errors)

        return result


class VehicleMillageViewSet(viewsets.ViewSet):
    permission_classes = [
        IsAuthenticated,
        HasRoleOrSuper("managers"),
    ]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Vehicle.objects.all()
        manager = Manager.objects.get(user=self.request.user)
        return Vehicle.objects.filter(enterprise__in=manager.enterprises.all())

    def list(self, request):
        vehicle_id = request.query_params.get("vehicle_id", None)
        period = request.query_params.get("period", None)
        start_date = request.query_params.get("start_date", None)
        end_date = request.query_params.get("end_date", None)
        output_format = "json"

        if not all([vehicle_id, period, start_date, end_date, output_format]):
            raise rest_serializers.ValidationError(
                "'Отсутствуют обязательные поля'"
            )

        if period not in ["day", "week", "month", "year"]:
            raise rest_serializers.ValidationError("'Неверный период'")

        try:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_datedatime = datetime.strptime(end_date, "%Y-%m-%d").date()

        except (ValueError, TypeError):
            raise rest_serializers.ValidationError(
                "'Неверный формат даты. Должен быть YYYY-MM-DD'"
            )

        vehicle = get_object_or_404(self.get_queryset(), pk=vehicle_id)
        if not request.user.is_superuser:
            manager = Manager.objects.get(user=self.request.user)
            is_belong_to_manager = (
                vehicle.enterprise.id
                in manager.enterprises.values_list("id", flat=True)
            )
            if not is_belong_to_manager:
                raise PermissionDenied(
                    detail="У вас нет доступа к этому автомобилю"
                )

        report = VehicleMileageReport(
            start_date=start_datetime,
            end_date=end_datedatime,
            period=period,
            vehicle=vehicle,
            enterprise=None,
        )

        report_data = report.generate()
        return Response(report_data)


class DetailBrandView(WebBrandMixin, DetailView):

    http_method_names = ["get"]
    template_name = "vehicles/brand_detail.html"
    permission_required = ["vehicles.view_brand"]
    context_object_name = "brand"

    def get_object(self, queryset=None):
        brand_name = self.kwargs.get("name")
        cache_key = f"brand_{brand_name}"

        brand = cache.get(cache_key)
        if brand is None:
            brand = Brand.objects.get(name=brand_name)
            cache.set(cache_key, brand, 60 * 30)

        return brand
