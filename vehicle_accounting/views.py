import ast
from functools import wraps
import uuid
import asyncio
import gpxpy
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, render, HttpResponseRedirect
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from datetime import datetime, timedelta
from django.views.generic import TemplateView
from asgiref.sync import sync_to_async
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import HttpResponse, Http404, JsonResponse
from django.core.cache import cache
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.db import transaction
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
    View,
)
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import ProtectedError
from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.renderers import JSONRenderer
from rest_framework import serializers as rest_serializers
import colorsys
import pytz
import folium
from io import StringIO, TextIOWrapper
from decimal import Decimal
import csv
import json
from .admin import VehicleResource, EnterpriseResource, TripResource
from .utils.time import str_iso_datetime_to_timezone
from .models import (
    Vehicle,
    Brand,
    Driver,
    Enterprise,
    VehicleDriver,
    Manager,
    VehicleGPSPoint,
    Trip,
)
from .serializers import (
    VehicleSerializer,
    BrandSerializer,
    DriverSerializer,
    EnterpriseSerializer,
    ActiveVehicleDriverSerializer,
    VehicleGPSPointSerializer,
    GeoJSONVehicleGPSPointSerializer,
    TripSerializer,
)
from .permissions import HasRoleOrSuper
from .forms import CustomLoginForm, VehicleForm
from .reports import (
    BaseReport,
    VehicleMileageReport,
    VehicleSalesReport,
    DriverAssignmentReport,
)
import hashlib


def cache_response(timeout=300, key_prefix="drf_cache"):
    """
    Декоратор для кеширования ответов DRF ViewSet
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            # Проверяем кеш только для GET запросов
            if request.method != "GET":
                response = view_func(self, request, *args, **kwargs)
                return response

            # Создаем уникальный ключ кеша
            cache_key_data = {
                "view": self.__class__.__name__,
                "action": getattr(self, "action", "unknown"),
                "method": request.method,
                "user_id": (
                    request.user.id
                    if request.user.is_authenticated
                    else "anonymous"
                ),
                "query_params": dict(request.query_params),
                "args": args,
                "kwargs": kwargs,
            }

            cache_key = f"{key_prefix}:{hashlib.md5(json.dumps(cache_key_data, sort_keys=True).encode()).hexdigest()}"
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return cached_response

            # Выполняем запрос
            response = view_func(self, request, *args, **kwargs)
            # Кешируем только успешные GET ответы
            if request.method == "GET" and response.status_code == 200:
                cache.set(cache_key, response, timeout)

            return response

        return wrapper

    return decorator


def custom_handler403(request, exception):

    return render(
        request=request,
        template_name="errors/error_page.html",
        status=403,
        context={
            "title": "Ошибка доступа: 403",
            "error_message": "Доступ к этой странице ограничен",
        },
    )


def custom_handler401(request, exception):

    return render(
        request=request,
        template_name="errors/error_page.html",
        status=401,
        context={
            "title": "Ошибка доступа: 401",
            "error_message": "Страница доступна только авторизированным пользователям",
        },
    )


class CustomLoginView(LoginView):
    form_class = CustomLoginForm


class CommonWebMixin(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin
):
    login_url = reverse_lazy("login")


class WebVehicleMixin(CommonWebMixin):
    model = Vehicle


class WebEnterpriseMixin(CommonWebMixin):
    model = Enterprise


class WebTripMixin(CommonWebMixin):
    model = Trip


class WebBrandMixin(CommonWebMixin):
    model = Brand


class VehicleAccountingPaginatiion(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 100


class IndexVehicleView(
    WebVehicleMixin,
    ListView,
):
    http_method_names = ["get"]
    context_object_name = "vehicles"
    template_name = "vehicles/vehicles_list.html"
    paginate_by = 100
    permission_required = ["vehicle_accounting.view_vehicle"]

    def get_queryset(self):
        queryset = Vehicle.objects.select_related("brand", "enterprise")

        if self.request.user.is_superuser:
            return queryset

        if hasattr(self.request.user, "manager"):
            enterprise_ids = self.request.user.manager.enterprises.values_list(
                "id", flat=True
            )
            return queryset.filter(enterprise_id__in=enterprise_ids)

        return Vehicle.objects.none()


class CreateVehicleView(WebVehicleMixin, CreateView):

    http_method_names = ["get", "post"]
    template_name = "vehicles/vehicles_create.html"
    success_url = reverse_lazy("vehicles_list")
    permission_required = ["vehicle_accounting.add_vehicle"]
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
    template_name = "vehicles/vehicles_update.html"
    success_url = reverse_lazy("vehicles_list")
    permission_required = [
        "vehicle_accounting.change_vehicle",
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
    template_name = "vehicles/vehicles_delete.html"
    permission_required = ["vehicle_accounting.change_vehicle"]
    context_object_name = "vehicle"
    success_url = reverse_lazy("vehicles_list")

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
    permission_required = ["vehicle_accounting.view_vehicle"]
    context_object_name = "vehicle"

    def has_permission(self):
        if self.request.user.is_superuser:
            return True
        if hasattr(self.request.user, "manager"):
            vehicle = self.get_object()
            manager = self.request.user.manager
            return vehicle.enterprise in manager.enterprises.all()
        return False


class DetailBrandView(WebBrandMixin, DetailView):

    http_method_names = ["get"]
    template_name = "brands/brand_detail.html"
    permission_required = ["vehicle_accounting.view_brand"]
    context_object_name = "brand"

    def get_object(self, queryset=None):
        brand_name = self.kwargs.get("name")
        cache_key = f"brand_{brand_name}"

        brand = cache.get(cache_key)
        if brand is None:
            brand = Brand.objects.get(name=brand_name)
            cache.set(cache_key, brand, 60 * 30)

        return brand

    def has_permission(self):
        return self.request.user.is_superuser or hasattr(
            self.request.user, "manager"
        )


class IndexEnterpisesView(WebEnterpriseMixin, ListView):
    http_method_names = ["get"]
    context_object_name = "enterprises"
    template_name = "enterprises/enterprises_list.html"
    paginate_by = 100
    permission_required = ["vehicle_accounting.view_enterprise"]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Enterprise.objects.all()
        manager = Manager.objects.get(user=self.request.user)
        return Enterprise.objects.filter(id__in=manager.enterprises.all())


class IndexEnterpiseVehiclesView(WebVehicleMixin, ListView):
    http_method_names = ["get"]
    context_object_name = "vehicles"
    template_name = "vehicles/vehicles_list_by_enterprise.html"
    paginate_by = 100
    permission_required = ["vehicle_accounting.view_vehicle"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["enterprise"] = Enterprise.objects.get(pk=self.kwargs["pk"])
        return context

    def has_permission(self):
        if self.request.user.is_superuser:
            return True
        if hasattr(self.request.user, "manager"):
            manager = self.request.user.manager
            return manager.enterprises.filter(pk=self.kwargs["pk"]).exists()
        return False

    def get_queryset(self):
        queryset = Vehicle.objects.select_related("brand")
        queryset = queryset.filter(enterprise=self.kwargs["pk"])
        return queryset


class TripMapView(WebTripMixin, View):
    http_method_names = ["post"]
    permission_required = ["vehicle_accounting.view_trip"]

    def get_distinct_colors_hex(self, n):
        """Генерирует список визуально различимых цветов"""
        colors = []
        for i in range(n):
            # Используем HSV для равномерного распределения по цветовому кругу
            h = i / n
            s = 0.8  # Насыщенность
            v = 0.9  # Яркость

            # Конвертируем HSV в RGB
            r, g, b = colorsys.hsv_to_rgb(h, s, v)

            # Конвертируем в HEX
            color = "#{:02x}{:02x}{:02x}".format(
                int(r * 255), int(g * 255), int(b * 255)
            )
            colors.append(color)
        return colors

    def post(self, request, *args, **kwargs):
        selected_trip_ids = request.POST.getlist("selected_trips")
        if not selected_trip_ids:
            messages.error(
                request, "Выберите хотя бы одну поездку для визуализации"
            )
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

        selected_trip_ids = [int(trip_id) for trip_id in selected_trip_ids]
        selected_trips = Trip.objects.filter(id__in=selected_trip_ids)
        colors = self.get_distinct_colors_hex(len(selected_trips))

        folium_map = folium.Map(tiles="OpenStreetMap")
        all_points = []

        for i, trip in enumerate(selected_trips):
            # Проверка доступа (если пользователь не суперпользователь)
            if not request.user.is_superuser:
                manager = request.user.manager
                if trip.vehicle.enterprise not in manager.enterprises.all():
                    raise PermissionDenied("У вас нет доступа к этой поездке")

            # Получаем все GPS точки для этой поездки
            current_points = VehicleGPSPoint.objects.filter(
                vehicle=trip.vehicle,
                created_at__gte=trip.start_time,
                created_at__lte=trip.end_time,
            ).order_by("created_at")

            # Объединяем текущие и архивные точки
            all_trip_points = list(current_points)
            all_trip_points.sort(key=lambda x: x.created_at)

            if not all_trip_points:
                continue

            # Извлекаем координаты для маршрута
            coordinates = [
                (point.point.y, point.point.x) for point in all_trip_points
            ]
            all_points.extend(coordinates)

            # Получаем цвет для этой поездки
            color = colors[i]

            # Добавляем трек на карту используя обычный PolyLine
            folium.PolyLine(
                locations=coordinates,
                popup=f"Поездка {trip.vehicle.car_number}: {trip.start_time.strftime('%d.%m.%Y %H:%M')} - {trip.end_time.strftime('%d.%m.%Y %H:%M')}",
                tooltip=f"Поездка {trip.vehicle.car_number}",
                color=color,
                weight=5,
                opacity=0.8,
            ).add_to(folium_map)

            # Добавляем маркеры начала и конца поездки
            if coordinates:
                # Начальная точка
                folium.Marker(
                    location=coordinates[0],
                    popup=f"Начало поездки {trip.id}: {trip.start_time.strftime('%d.%m.%Y %H:%M')}",
                    icon=folium.Icon(color="green", icon="play"),
                ).add_to(folium_map)

                # Конечная точка
                folium.Marker(
                    location=coordinates[-1],
                    popup=f"Конец поездки {trip.id}: {trip.end_time.strftime('%d.%m.%Y %H:%M')}",
                    icon=folium.Icon(color="red", icon="stop"),
                ).add_to(folium_map)
        map_html = folium_map._repr_html_()
        return render(
            request,
            "trip/trip_map.html",
            {"map_html": map_html, "selected_trips": selected_trips},
        )


class VehicleViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    serializer_class = VehicleSerializer
    pagination_class = VehicleAccountingPaginatiion
    filter_backends = [OrderingFilter]
    ordering_fields = ["id", "price", "created_at"]
    permission_classes = [
        IsAuthenticated,
        HasRoleOrSuper("manager"),
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
        "vehicle_accounting.view_vehicle",
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
        vehicle_id = self.request.GET.get("vehicle_id")
        if vehicle_id is not None:
            queryset = queryset.filter(id=vehicle_id)

        if self.request.user.is_superuser:
            return queryset
        manager = Manager.objects.get(user=self.request.user)
        queryset = queryset.filter(enterprise__in=manager.enterprises.all())
        enterprise_id = self.request.GET.get("enterprise_id")
        if enterprise_id is not None:
            queryset = queryset.filter(enterprise__id=enterprise_id)

        return queryset


class ExportEnterprises(LoginRequiredMixin, PermissionRequiredMixin, View):
    model = Enterprise
    permission_required = [
        "vehicle_accounting.view_enterprises",
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


class ExportTrips(LoginRequiredMixin, PermissionRequiredMixin, View):
    model = Trip
    permission_required = [
        "vehicle_accounting.view_trip",
    ]

    def get(self, request, *args, **kwargs):
        export_format = request.GET.get("export_format", "csv")
        dataset = TripResource().export(self.get_queryset())
        if export_format == "json":
            response = HttpResponse(dataset.json, content_type="json")
            response["Content-Disposition"] = "attachment; filename=trips.json"
        else:
            response = HttpResponse(dataset.csv, content_type="csv")
            response["Content-Disposition"] = "attachment; filename=trips.csv"

        return response

    def get_queryset(self):
        queryset = Trip.objects.all()
        queryset = queryset.filter(vehicle__id=self.kwargs["vehicle_id"])
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        queryset = queryset.filter(
            start_time__date__gte=start_date,
            end_time__date__lte=end_date,
        )
        if self.request.user.is_superuser:
            return queryset
        manager = Manager.objects.get(user=self.request.user)
        queryset = queryset.filter(
            vehicle__enterprise__in=manager.enterprises.all()
        )
        return queryset


class BrandViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    pagination_class = VehicleAccountingPaginatiion
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


class DriverViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    serializer_class = DriverSerializer
    pagination_class = VehicleAccountingPaginatiion
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


class EnterpriseViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    serializer_class = EnterpriseSerializer
    pagination_class = VehicleAccountingPaginatiion
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
            return Enterprise.objects.all()
        manager = Manager.objects.get(user=self.request.user)
        return Enterprise.objects.filter(id__in=manager.enterprises.all())

    def get_all(self):
        return Enterprise.objects.all()

    def get_object(self):
        obj = get_object_or_404(self.get_all(), pk=self.kwargs["pk"])
        if obj not in self.get_queryset():
            raise PermissionDenied(
                detail="You do not have permission to access this object."
            )
        return obj


class VehicleMillageViewSet(viewsets.ViewSet):
    permission_classes = [
        IsAuthenticated,
        HasRoleOrSuper("manager"),
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


class ActiveVehicleDriverViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    serializer_class = ActiveVehicleDriverSerializer
    pagination_class = VehicleAccountingPaginatiion
    permission_classes = [
        IsAuthenticated,
        HasRoleOrSuper("manager"),
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


class VehicleGPSPointViewSet(viewsets.ViewSet):

    permission_classes = [
        IsAuthenticated,
        HasRoleOrSuper("manager"),
    ]

    def list(self, request):
        vehicle_id = request.query_params.get("vehicle_id", None)
        start_date = request.query_params.get("start_date", None)
        end_date = request.query_params.get("end_date", None)
        output_format = request.query_params.get("output_format", "json")

        if vehicle_id is None:
            raise rest_serializers.ValidationError(
                "'vehicle_id' parameter is required"
            )
        if start_date is None:
            raise rest_serializers.ValidationError(
                "'start_date' parameter is required"
            )
        if end_date is None:
            raise rest_serializers.ValidationError(
                "'end_date' parameter is required"
            )
        if start_date > end_date:
            raise rest_serializers.ValidationError(
                "'start_date' cant be greater than 'end_date'"
            )

        if not request.user.is_superuser:
            manager = Manager.objects.get(user=self.request.user)
            is_belong_to_manager = Vehicle.objects.filter(
                id=vehicle_id, enterprise__in=manager.enterprises.all()
            ).exists()
            if not is_belong_to_manager:
                raise PermissionDenied(
                    detail="You do not have permission to access this object."
                )

        current_points = VehicleGPSPoint.objects.filter(
            vehicle_id=vehicle_id,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        )
        if output_format == "geojson":
            data = GeoJSONVehicleGPSPointSerializer(
                current_points, many=True
            ).data
        else:
            data = VehicleGPSPointSerializer(current_points, many=True).data
        return Response(data)


class TripViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    serializer_class = TripSerializer
    permission_classes = [
        IsAuthenticated,
        HasRoleOrSuper("manager"),
    ]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Trip.objects.all()
        manager = Manager.objects.get(user=self.request.user)
        return Trip.objects.filter(
            vehicle__enterprise__in=manager.enterprises.all()
        )

    def get_all(self):
        return Trip.objects.all()

    def get_object(self):
        obj = get_object_or_404(self.get_all(), pk=self.kwargs["pk"])
        if obj not in self.get_queryset():
            raise PermissionDenied(
                detail="You do not have permission to access this object."
            )
        return obj


class TripGPSPointViewSet(viewsets.ViewSet):

    permission_classes = [
        IsAuthenticated,
        HasRoleOrSuper("manager"),
    ]

    def list(self, request):
        # Получаем параметры запроса
        vehicle_id = request.query_params.get("vehicle_id", None)
        start_date = request.query_params.get("start_date", None)
        end_date = request.query_params.get("end_date", None)
        output_format = request.query_params.get("output_format", "json")

        # Проверяем обязательные параметры
        if vehicle_id is None:
            raise rest_serializers.ValidationError(
                "'vehicle_id' parameter is required"
            )
        if start_date is None:
            raise rest_serializers.ValidationError(
                "'start_date' parameter is required"
            )
        if end_date is None:
            raise rest_serializers.ValidationError(
                "'end_date' parameter is required"
            )
        if start_date > end_date:
            raise rest_serializers.ValidationError(
                "'start_date' can't be greater than 'end_date'"
            )

        if not request.user.is_superuser:
            manager = Manager.objects.get(user=request.user)
            is_belong_to_manager = Vehicle.objects.filter(
                id=vehicle_id, enterprise__in=manager.enterprises.all()
            ).exists()
            if not is_belong_to_manager:
                raise PermissionDenied(
                    detail="You do not have permission to access this vehicle."
                )

        vehicle = Vehicle.objects.get(id=vehicle_id)
        enterprise_timezone = pytz.timezone(vehicle.enterprise.timezone)
        start_datetime_utc = str_iso_datetime_to_timezone(
            start_date, enterprise_timezone, pytz.UTC
        )
        end_datetime_utc = str_iso_datetime_to_timezone(
            end_date, enterprise_timezone, pytz.UTC
        )
        if start_datetime_utc is None or end_datetime_utc is None:
            raise rest_serializers.ValidationError(
                "Invalid date format. Use ISO format YYYY-MM-DDTHH:MM:SS"
            )
        trips = Trip.objects.filter(
            vehicle_id=vehicle_id,
            start_time__gte=start_datetime_utc,
            end_time__lte=end_datetime_utc,
        ).order_by("start_time")

        if not trips.exists() and output_format == "geojson":
            return Response({"type": "FeatureCollection", "features": []})
        elif not trips.exists():
            return Response([{}])

        query_current_points = VehicleGPSPoint.objects.none()
        for trip in trips:

            query_current_points = (
                query_current_points
                | VehicleGPSPoint.objects.filter(
                    vehicle_id=vehicle_id,
                    created_at__gte=trip.start_time,
                    created_at__lte=trip.end_time,
                )
            )

        query_all_tracks_points = query_current_points.order_by("created_at")

        if output_format == "geojson":
            result_points = GeoJSONVehicleGPSPointSerializer(
                query_all_tracks_points, many=True
            ).data["features"]
            return Response(
                {
                    "type": "FeatureCollection",
                    "features": result_points,
                }
            )

        result_points = VehicleGPSPointSerializer(
            query_all_tracks_points, many=True
        ).data
        return Response(result_points)


class TripListViewSet(viewsets.ViewSet):
    permission_classes = [
        IsAuthenticated,
        HasRoleOrSuper("manager"),
    ]

    def list(self, request):
        vehicle_id = request.query_params.get("vehicle_id", None)
        start_date = request.query_params.get("start_date", None)
        end_date = request.query_params.get("end_date", None)

        if vehicle_id is None:
            raise rest_serializers.ValidationError(
                "'vehicle_id' parameter is required"
            )
        if start_date is None:
            raise rest_serializers.ValidationError(
                "'start_date' parameter is required"
            )
        if end_date is None:
            raise rest_serializers.ValidationError(
                "'end_date' parameter is required"
            )

        if not request.user.is_superuser:
            manager = Manager.objects.get(user=request.user)
            is_belong_to_manager = Vehicle.objects.filter(
                id=vehicle_id, enterprise__in=manager.enterprises.all()
            ).exists()
            if not is_belong_to_manager:
                raise PermissionDenied(
                    detail="You do not have permission to access this vehicle."
                )

        vehicle = Vehicle.objects.get(id=vehicle_id)
        enterprise_timezone = pytz.timezone(vehicle.enterprise.timezone)

        start_datetime_utc = str_iso_datetime_to_timezone(
            start_date, enterprise_timezone, pytz.UTC
        )
        end_datetime_utc = str_iso_datetime_to_timezone(
            end_date, enterprise_timezone, pytz.UTC
        )
        if start_datetime_utc is None or end_datetime_utc is None:
            raise rest_serializers.ValidationError(
                "Invalid date format. Use ISO format YYYY-MM-DDTHH:MM:SS"
            )
        trips = Trip.objects.filter(
            vehicle_id=vehicle_id,
            start_time__gte=start_datetime_utc,
            end_time__lte=end_datetime_utc,
        ).order_by("start_time")

        serializer = TripSerializer(trips, many=True)
        return Response(serializer.data)


class ImportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = None
    success_url = None
    permission_required = []

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()

        if "import_file" not in request.FILES:
            messages.error(request, "Файл не был загружен")
            return render(request, self.template_name, context)

        import_file = request.FILES["import_file"]
        import_format = request.POST.get("import_format", "json")
        update_existing = request.POST.get("update_existing") == "on"

        try:
            if import_format == "csv":
                data = self.parse_csv(import_file)
            elif import_format == "gpx":
                data = self.parse_gpx(import_file)
            else:  # json
                data = self.parse_json(import_file)
        except Exception as e:
            error_message = f"Ошибка при разборе файла: {str(e)}"
            messages.error(request, error_message)
            context["result_message"] = error_message
            context["message_type"] = "danger"
            return render(request, self.template_name, context)

        with transaction.atomic():
            import_savepoint = transaction.savepoint()
            results = self.process_data(data, update_existing, request)
            if not results["success"]:
                transaction.savepoint_rollback(import_savepoint)
            else:
                transaction.savepoint_commit(import_savepoint)

        if results["success"]:
            created_count = results["created_count"]
            updated_count = results["updated_count"]
            messages.success(
                request,
                f"Импорт завершен. Создано: {created_count}, Обновлено: {updated_count}",
            )
            context["message_type"] = "success"
        else:
            error_message = results["message"]
            error_count = results["error_count"]
            messages.error(
                request,
                f"Импорт не выполнен. Ошибок: {error_count}. {error_message}",
            )
            context["message_type"] = "danger"
        context["result_message"] = results["message"]
        return render(request, self.template_name, context)

    def get_context_data(self):
        return {}

    def parse_csv(self, file):
        csv_file = TextIOWrapper(file, encoding="utf-8-sig")
        reader = csv.DictReader(csv_file)
        return list(reader)

    def parse_json(self, file):
        json_text = file.read().decode("utf-8")
        return json.loads(json_text)

    def parse_gpx(self, file):
        gpx_file = TextIOWrapper(file, encoding="utf-8-sig")
        gpx = gpxpy.parse(gpx_file)
        parsed_gpx = []
        for trk in gpx.tracks:
            track = {
                "uuid": None,
                "vehicle_uuid": None,
                "start_time": None,
                "end_time": None,
                "start_point": None,
                "end_point": None,
                "track_points": [],
            }

            start_point = None
            if trk.segments[0].points:
                start_point = trk.segments[0].points[0]
                track["start_point"] = (
                    f"({start_point.latitude}, {start_point.longitude})"
                )
                track["start_time"] = start_point.time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

            i = len(trk.segments) - 1
            end_point = None
            while i >= 0 and end_point is None:
                if trk.segments[i].points:
                    end_point = trk.segments[i].points[-1]
                    track["end_point"] = (
                        f"({end_point.latitude}, {end_point.longitude})"
                    )
                    track["end_time"] = end_point.time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                i -= 1

            for segment in trk.segments:
                for point in segment.points:
                    if point in (start_point, end_point):
                        continue
                    track["track_points"].append(
                        f"({point.latitude}, {point.longitude})"
                    )

            parsed_gpx.append(track)
        return parsed_gpx

    def process_data(self, data, update_existing, request):
        raise NotImplementedError(
            "Subclasses must implement process_data method"
        )


class ImportEnterpriseView(ImportView):
    template_name = "enterprises/enterprises_import.html"
    success_url = reverse_lazy("enterprises_list")
    permission_required = ["vehicle_accounting.add_enterprises"]

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


class ImportVehicleView(ImportView):
    template_name = "vehicles/vehicles_import.html"
    success_url = reverse_lazy("vehicles_list")
    permission_required = ["vehicle_accounting.add_vehicle"]

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
        }

        if errors:
            result["message"] += "\n\nОшибки:\n" + "\n".join(errors)

        return result


class ImportTripView(ImportView):
    template_name = "trip/trips_import.html"
    permission_required = ["vehicle_accounting.add_trip"]

    def get_success_url(self):
        vehicle_id = self.kwargs.get("vehicle_id")
        if vehicle_id:
            return reverse_lazy("vehicle_detail", kwargs={"pk": vehicle_id})
        return reverse_lazy("vehicles_list")

    def parse_coordinates(self, coord_str):
        """Парсинг координат из строки формата '(lat, lng)' в tuple (lat, lng)"""
        if not coord_str or not isinstance(coord_str, str):
            return None

        # Удаляем скобки и пробелы, затем разделяем по запятой
        coord_str = coord_str.strip("() \t\n\r")
        parts = coord_str.split(",")

        if len(parts) != 2:
            return None

        try:
            lat = float(parts[0].strip())
            lng = float(parts[1].strip())
            return (lat, lng)
        except (ValueError, TypeError):
            return None

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
                # Получаем автомобиль
                vehicle_id = self.kwargs["vehicle_id"]
                vehicle = None
                try:
                    vehicle = Vehicle.objects.get(id=vehicle_id)
                except (Vehicle.DoesNotExist, ValueError):
                    pass
                if not vehicle:
                    error_count += 1
                    errors.append(
                        f"Не удалось определить автомобиль для поездки: {row}"
                    )
                    continue

                # Проверяем права доступа
                if (
                    not request.user.is_superuser
                    and vehicle.enterprise.id not in allowed_enterprises
                ):
                    error_count += 1
                    errors.append(
                        f"У вас нет прав на добавление поездок для автомобиля: {vehicle.car_number}"
                    )
                    continue

                trip_uuid = row.get("uuid", None)
                start_time_str = row.get("start_time")
                end_time_str = row.get("end_time")
                end_time_str = row.get("end_time")
                track_points = []
                if request.POST.get("import_format") == "gpx":
                    track_points = row.get("track_points")

                if not all([start_time_str, end_time_str]):
                    error_count += 1
                    errors.append(
                        f"Отсутствуют обязательные поля для поездки: {row}"
                    )
                    continue

                # Преобразуем строки времени в datetime объекты
                try:
                    start_time = datetime.strptime(
                        start_time_str, "%Y-%m-%d %H:%M:%S"
                    )
                    end_time = datetime.strptime(
                        end_time_str, "%Y-%m-%d %H:%M:%S"
                    )

                    # Добавляем информацию о часовом поясе, если её нет
                    if start_time.tzinfo is None:
                        tz = pytz.timezone(vehicle.enterprise.timezone)
                        start_time = tz.localize(start_time)
                    if end_time.tzinfo is None:
                        tz = pytz.timezone(vehicle.enterprise.timezone)
                        end_time = tz.localize(end_time)

                except Exception as e:
                    error_count += 1
                    errors.append(
                        f"Ошибка при обработке даты/времени: {str(e)}"
                    )
                    continue

                # Проверяем, что время начала раньше времени окончания
                if start_time > end_time:
                    error_count += 1
                    errors.append(
                        f"Время начала поездки должно быть раньше времени окончания: {row}"
                    )
                    continue

                # Обрабатываем координаты
                start_point = None
                end_point = None

                # Проверяем наличие координат в формате строки "(lat, lng)"
                start_coords_str = row.get("start_point")
                end_coords_str = row.get("end_point")

                # Парсим координаты из строки, если они указаны
                start_coords = self.parse_coordinates(start_coords_str)
                end_coords = self.parse_coordinates(end_coords_str)

                # Создаем или находим точки GPS
                existing_start_point = None
                if start_coords:
                    existing_start_point = VehicleGPSPoint.objects.filter(
                        vehicle=vehicle,
                        point=Point(
                            start_coords[1], start_coords[0]
                        ),  # Point(lng, lat)
                        created_at=start_time,
                    ).first()

                start_point = None
                if existing_start_point:
                    start_point = existing_start_point
                elif start_coords:
                    start_point = VehicleGPSPoint.objects.create(
                        vehicle=vehicle,
                        point=Point(
                            start_coords[1], start_coords[0]
                        ),  # Point(lng, lat)
                        created_at=start_time,
                    )
                    start_point.created_at = start_time
                    start_point.save()

                existing_end_point = None
                if end_coords:
                    existing_end_point = VehicleGPSPoint.objects.filter(
                        vehicle=vehicle,
                        point=Point(
                            end_coords[1], end_coords[0]
                        ),  # Point(lng, lat)
                        created_at=end_time,
                    ).first()

                end_point = None
                if existing_end_point:
                    end_point = existing_end_point
                elif end_coords:
                    end_point = VehicleGPSPoint.objects.create(
                        vehicle=vehicle,
                        point=Point(
                            end_coords[1], end_coords[0]
                        ),  # Point(lng, lat)
                    )
                    end_point.created_at = end_time
                    end_point.save()

                # Проверяем существование поездки
                existing_trip = None
                if trip_uuid:
                    try:
                        existing_trip = Trip.objects.filter(
                            uuid=trip_uuid
                        ).first()
                    except (Trip.DoesNotExist, ValueError):
                        pass

                if not trip_uuid:
                    trip_uuid = uuid.uuid4()

                if existing_trip and update_existing:
                    existing_trip.start_point = start_point
                    existing_trip.end_point = end_point
                    existing_trip.save()
                    updated_count += 1

                if not existing_trip and self.is_trip_overlap_any(
                    vehicle.id, start_time, end_time
                ):
                    error_count += 1
                    errors.append(
                        f"Поездка пересекается с другой поездкой: {row}"
                    )
                    continue
                if not existing_trip:
                    Trip.objects.create(
                        uuid=trip_uuid,
                        vehicle=vehicle,
                        start_time=start_time,
                        end_time=end_time,
                        start_point=start_point,
                        end_point=end_point,
                    )
                    created_count += 1

                if not existing_trip and track_points:
                    gps_points = [
                        VehicleGPSPoint(vehicle=vehicle, point=Point(lng, lat))
                        for lat, lng in [
                            self.parse_coordinates(point)
                            for point in track_points
                        ]
                    ]
                    VehicleGPSPoint.objects.bulk_create(gps_points)

            except Exception as e:
                error_count += 1
                errors.append(f"Ошибка при обработке строки {row}: {str(e)}")

        result = {
            "success": error_count == 0,
            "message": f"Импорт завершен. Создано: {created_count}, Обновлено: {updated_count}, Ошибок: {error_count}",
        }

        if errors:
            result["message"] += "\n\nОшибки:\n" + "\n".join(errors)

        return result

    def is_trip_overlap_any(self, vehicle_id, start_time, end_time):
        return Trip.objects.filter(
            vehicle__id=vehicle_id,
            start_time__lt=end_time,
            end_time__gt=start_time,
        ).exists()


class ReportBaseView(LoginRequiredMixin, PermissionRequiredMixin):
    template_name = None
    permission_required = [
        "vehicle_accounting.view_vehicle",
        "vehicle_accounting.view_driver",
        "vehicle_accounting.view_brand",
        "vehicle_accounting.view_enterprise",
        "vehicle_accounting.view_trip",
    ]

    def get_enterprises(self):
        if self.request.user.is_superuser:
            return Enterprise.objects.all()
        return self.request.user.manager.enterprises.all()

    def get_vehicles(self):
        if self.request.user.is_superuser:
            return Vehicle.objects.all()
        return Vehicle.objects.filter(enterprise__in=self.get_enterprises())

    def get_brands(self):
        return Brand.objects.all()


class ReportListView(ReportBaseView, TemplateView):
    template_name = "reports/report_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = datetime.now().date()
        month_ago = today - timedelta(days=30)

        context.update(
            {
                "enterprises": self.get_enterprises(),
                "vehicles": self.get_vehicles(),
                "brands": self.get_brands(),
                "period_choices": BaseReport.PERIOD_CHOICES,
                "default_start_date": month_ago.strftime("%Y-%m-%d"),
                "default_end_date": today.strftime("%Y-%m-%d"),
            }
        )

        return context

    def post(self, request, *args, **kwargs):
        report_type = request.POST.get("report_type")

        if report_type not in [
            "vehicle_mileage",
            "vehicle_sales",
            "driver_assignment",
        ]:
            return self.render_to_response(
                self.get_context_data(error="Неверный тип отчета")
            )

        # Get common parameters
        try:
            start_date = datetime.strptime(
                request.POST.get("start_date"), "%Y-%m-%d"
            ).date()
            end_date = datetime.strptime(
                request.POST.get("end_date"), "%Y-%m-%d"
            ).date()
        except (ValueError, TypeError):
            return self.render_to_response(
                self.get_context_data(error="Неверный формат даты")
            )

        period = request.POST.get("period")
        if period not in ["day", "week", "month", "year"]:
            return self.render_to_response(
                self.get_context_data(error="Неверный период")
            )

        # Prepare the URL parameters
        url_params = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "period": period,
        }

        # Add report-specific parameters
        if report_type == "vehicle_mileage":
            vehicle_id = request.POST.get("vehicle_id")
            enterprise_id = request.POST.get("mileage_enterprise_id")

            if vehicle_id:
                url_params["vehicle_id"] = vehicle_id
            elif enterprise_id:
                url_params["enterprise_id"] = enterprise_id
            else:
                return self.render_to_response(
                    self.get_context_data(
                        error="Необходимо выбрать автомобиль или предприятие"
                    )
                )

        if report_type == "vehicle_sales":
            brand_id = request.POST.get("brand_id")
            enterprise_id = request.POST.get("sales_enterprise_id")

            if brand_id:
                url_params["brand_id"] = brand_id
            if enterprise_id:
                url_params["enterprise_id"] = enterprise_id

        if report_type == "driver_assignment":
            enterprise_ids = request.POST.getlist("enterprise_id")
            enterprise_ids = ",".join(enterprise_ids)
            if enterprise_ids:
                url_params["enterprise_ids"] = enterprise_ids

        url = reverse(f"report_{report_type}")
        param_string = "&".join([f"{k}={v}" for k, v in url_params.items()])

        return HttpResponseRedirect(f"{url}?{param_string}")


class VehicleMileageReportView(ReportBaseView, TemplateView):
    template_name = "reports/vehicle_mileage_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get parameters from request
        try:
            start_date = datetime.strptime(
                self.request.GET.get("start_date"), "%Y-%m-%d"
            ).date()
            end_date = datetime.strptime(
                self.request.GET.get("end_date"), "%Y-%m-%d"
            ).date()
        except (ValueError, TypeError):
            context["error"] = "Неверный формат даты"
            return context

        period = self.request.GET.get("period", "day")
        vehicle_id = self.request.GET.get("vehicle_id")
        enterprise_id = self.request.GET.get("enterprise_id")

        vehicle = None
        enterprise = None

        if vehicle_id:
            vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        if vehicle_id and not self.request.user.is_superuser:
            user_enterprises = self.request.user.manager.enterprises.all()
            if vehicle.enterprise not in user_enterprises:
                context["error"] = "У вас нет доступа к данному автомобилю"
                return context

        if enterprise_id:
            enterprise = get_object_or_404(Enterprise, id=enterprise_id)
        if enterprise_id and not self.request.user.is_superuser:
            user_enterprises = self.request.user.manager.enterprises.all()
            if enterprise not in user_enterprises:
                context["error"] = "У вас нет доступа к данному предприятию"
                return context

        report = VehicleMileageReport(
            start_date=start_date,
            end_date=end_date,
            period=period,
            vehicle=vehicle,
            enterprise=enterprise,
        )

        report_data = report.generate()

        context.update(
            {
                "report": report_data,
                "start_date": start_date,
                "end_date": end_date,
                "period": period,
                "period_label": dict(report.PERIOD_CHOICES).get(period, period),
                "vehicle": vehicle,
                "enterprise": enterprise,
            }
        )

        return context


class VehicleSalesReportView(ReportBaseView, TemplateView):
    template_name = "reports/vehicle_sales_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get parameters from request
        try:
            start_date = datetime.strptime(
                self.request.GET.get("start_date"), "%Y-%m-%d"
            ).date()
            end_date = datetime.strptime(
                self.request.GET.get("end_date"), "%Y-%m-%d"
            ).date()
        except (ValueError, TypeError):
            context["error"] = "Неверный формат даты"
            return context

        period = self.request.GET.get("period", "day")
        brand_id = self.request.GET.get("brand_id")
        enterprise_id = self.request.GET.get("enterprise_id")

        brand = None
        enterprise = None

        if brand_id:
            brand = get_object_or_404(Brand, id=brand_id)

        if enterprise_id:
            enterprise = get_object_or_404(Enterprise, id=enterprise_id)
        if enterprise_id and not self.request.user.is_superuser:
            user_enterprises = self.request.user.manager.enterprises.all()
            if enterprise not in user_enterprises:
                context["error"] = "У вас нет доступа к данному предприятию"
                return context

        # Generate report
        report = VehicleSalesReport(
            start_date=start_date,
            end_date=end_date,
            period=period,
            brand=brand,
            enterprise=enterprise,
        )

        # Get report data
        report_data = report.generate()

        # Add report and parameters to context
        context.update(
            {
                "report": report_data,
                "start_date": start_date,
                "end_date": end_date,
                "period": period,
                "period_label": dict(report.PERIOD_CHOICES).get(period, period),
                "brand": brand,
                "enterprise": enterprise,
            }
        )

        return context


class DriverAssignmentReportView(ReportBaseView, TemplateView):
    """View for displaying the driver assignment report"""

    template_name = "reports/driver_assignment_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get parameters from request
        try:
            start_date = datetime.strptime(
                self.request.GET.get("start_date"), "%Y-%m-%d"
            ).date()
            end_date = datetime.strptime(
                self.request.GET.get("end_date"), "%Y-%m-%d"
            ).date()
        except (ValueError, TypeError):
            context["error"] = "Неверный формат даты"
            return context

        period = self.request.GET.get("period", "day")
        enterprise_ids = self.request.GET.get("enterprise_ids").split(",")
        enterprises = []

        for enterprise_id in enterprise_ids:
            enterprise = get_object_or_404(Enterprise, id=enterprise_id)

            # Проверка прав доступа
            if not self.request.user.is_superuser:
                user_enterprises = self.request.user.manager.enterprises.all()
                if enterprise not in user_enterprises:
                    context["error"] = (
                        f"У вас нет доступа к предприятию: {enterprise.name}"
                    )
                    return context

            enterprises.append(enterprise)

        if not enterprises and self.request.user.is_superuser:
            enterprises = list(Enterprise.objects.all())
        if not enterprises and not self.request.user.is_superuser:
            enterprises = list(self.request.user.manager.enterprises.all())
        if not enterprises:
            context["error"] = "Нет доступных предприятий"
            return context

        report = DriverAssignmentReport(
            start_date=start_date,
            end_date=end_date,
            period=period,
            enterprises=enterprises,
        )
        report_data = report.generate()

        context.update(
            {
                "report": report_data,
                "start_date": start_date,
                "end_date": end_date,
                "period": period,
                "period_label": dict(report.PERIOD_CHOICES).get(period, period),
                "enterprises": enterprises,
            }
        )

        return context


@method_decorator(csrf_exempt, name="dispatch")
class AsyncGPSReceiveView(View):
    """Асинхронный Class-Based View для приема GPS данных"""

    async def post(self, request):
        """Асинхронный POST метод"""
        try:
            # Парсим данные из запроса
            try:
                gps_data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse(
                    {"status": "error", "message": "Некорректный JSON"},
                    status=400,
                    json_dumps_params={"ensure_ascii": False},
                )

            # Асинхронная валидация данных
            validation_result = await self.validate_gps_data(gps_data)
            if not validation_result["valid"]:
                return JsonResponse(
                    {"status": "error", "message": validation_result["error"]},
                    status=400,
                    json_dumps_params={"ensure_ascii": False},
                )

            # Запускаем обработку в фоновом режиме
            asyncio.create_task(self.process_gps_data_async(gps_data))

            # Сразу отвечаем клиенту
            return JsonResponse(
                {
                    "status": "success",
                    "message": "GPS данные приняты для обработки",
                    "vehicle_id": gps_data["vehicle_id"],
                    "received_at": datetime.now().isoformat(),
                },
                json_dumps_params={"ensure_ascii": False},
            )

        except Exception:
            return JsonResponse(
                {"status": "error", "message": "Внутренняя ошибка сервера"},
                status=500,
                json_dumps_params={"ensure_ascii": False},
            )

    async def validate_gps_data(self, gps_data):
        """Асинхронная валидация GPS данных"""
        # Проверка обязательных полей
        required_fields = ["vehicle_id", "latitude", "longitude"]
        if not all(field in gps_data for field in required_fields):
            return {
                "valid": False,
                "error": f"Отсутствуют обязательные поля: {required_fields}",
            }

        # Проверка типов данных
        try:
            vehicle_id = int(gps_data["vehicle_id"])
            latitude = float(gps_data["latitude"])
            longitude = float(gps_data["longitude"])
        except (ValueError, TypeError):
            return {"valid": False, "error": "Некорректные типы данных"}

        # Асинхронная проверка существования машины
        vehicle_exists = await sync_to_async(
            Vehicle.objects.filter(id=vehicle_id).exists
        )()

        if not vehicle_exists:
            return {
                "valid": False,
                "error": "Не существует машины с заданным vehicle_id",
            }

        # Проверка диапазона координат
        if latitude < -90 or latitude > 90:
            return {
                "valid": False,
                "error": f"Широта должна быть в диапазоне -90..90, получено: {latitude}",
            }
        if longitude < -180 or longitude > 180:
            return {
                "valid": False,
                "error": f"Долгота должна быть в диапазоне -180..180, получено: {longitude}",
            }

        return {"valid": True}

    async def process_gps_data_async(self, gps_data):
        """Асинхронная обработка GPS данных"""
        await asyncio.sleep(60)
        try:
            await self.save_gps_point_async(gps_data)
        except Exception as e:
            # Логирование ошибки
            print(f"Ошибка при сохранении GPS точки: {e}")

    async def save_gps_point_async(self, gps_data):
        """Асинхронное сохранение GPS точки"""
        try:
            vehicle = await sync_to_async(Vehicle.objects.get)(
                id=gps_data["vehicle_id"]
            )

            # Создаем точку
            point = Point(
                float(gps_data["longitude"]), float(gps_data["latitude"])
            )

            # Создаем и сохраняем GPS точку асинхронно
            gps_point = VehicleGPSPoint(vehicle=vehicle, point=point)
            await sync_to_async(gps_point.save)()

        except Vehicle.DoesNotExist:
            print(f"Машина с ID {gps_data['vehicle_id']} не найдена")
        except Exception as e:
            print(f"Ошибка при сохранении GPS точки: {e}")
