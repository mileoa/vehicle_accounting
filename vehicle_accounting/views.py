from django.shortcuts import get_object_or_404, render, HttpResponseRedirect
from django.core.serializers import serialize
from datetime import datetime
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import HttpResponse, Http404
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
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
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets
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
from .settings import DAYS_TO_MOVE_VEHICLE_GPS_TO_ARCHIVE
from .models import (
    Vehicle,
    Brand,
    Driver,
    Enterprise,
    VehicleDriver,
    Manager,
    VehicleGPSPoint,
    VehicleGPSPointArchive,
    Trip,
)
from .serializers import (
    VehicleSerializer,
    BrandSerializer,
    DriverSerializer,
    EnterpriseSerializer,
    ActiveVehicleDriverSerializer,
    VehicleGPSPointSerializer,
    VehicleGPSPointArchiveSerializer,
    GeoJSONVehicleGPSPointSerializer,
    GeoJSONGPSPointArchiveSerializer,
    TripSerializer,
)
from .permissions import HasRoleOrSuper
from .forms import CustomLoginForm, VehicleForm


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


class IndexVehicleView(
    WebVehicleMixin,
    ListView,
):
    http_method_names = ["get"]
    context_object_name = "vehicles"
    template_name = "vehicles/vehicles_list.html"
    permission_required = ["vehicle_accounting.view_vehicle"]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Vehicle.objects.all()
        manager = Manager.objects.get(user=self.request.user)
        return Vehicle.objects.filter(enterprise__in=manager.enterprises.all())


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
        vehicle = self.get_object()
        manager = self.request.user.manager
        return vehicle.enterprise in manager.enterprises.all()


class DeleteVehicleView(WebVehicleMixin, DeleteView):

    http_method_names = ["get", "post"]
    template_name = "vehicles/vehicles_delete.html"
    permission_required = ["vehicle_accounting.change_vehicle"]
    context_object_name = "vehicle"
    success_url = reverse_lazy("vehicles_list")

    def has_permission(self):
        if self.request.user.is_superuser:
            return True
        vehicle = self.get_object()
        manager = self.request.user.manager
        return vehicle.enterprise in manager.enterprises.all()

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
        vehicle = self.get_object()
        manager = self.request.user.manager
        return vehicle.enterprise in manager.enterprises.all()


class IndexEnterpisesView(WebEnterpriseMixin, ListView):
    http_method_names = ["get"]
    context_object_name = "enterprises"
    template_name = "enterprises/enterprises_list.html"
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
    permission_required = ["vehicle_accounting.view_vehicle"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["enterprise"] = Enterprise.objects.get(pk=self.kwargs["pk"])
        return context

    def has_permission(self):
        if self.request.user.is_superuser:
            return True
        manager = self.request.user.manager
        return manager.enterprises.filter(pk=self.kwargs["pk"]).exists()

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Vehicle.objects.all()
        manager = Manager.objects.get(user=self.request.user)
        return Vehicle.objects.filter(enterprise=self.kwargs["pk"])


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

            archived_points = VehicleGPSPointArchive.objects.filter(
                vehicle=trip.vehicle,
                created_at__gte=trip.start_time,
                created_at__lte=trip.end_time,
            ).order_by("created_at")

            # Объединяем текущие и архивные точки
            all_trip_points = list(current_points) + list(archived_points)
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


class VehicleAccountingPaginatiion(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 100


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


class ExportVehicles(LoginRequiredMixin, View):
    model = Vehicle

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


class ExportVehicles(LoginRequiredMixin, View):
    model = Vehicle

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


class ExportEnterprises(LoginRequiredMixin, View):
    model = Enterprise

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


class ExportTrips(LoginRequiredMixin, View):
    model = Trip

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


class DriverViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]
    serializer_class = DriverSerializer
    pagination_class = VehicleAccountingPaginatiion
    permission_classes = [
        IsAuthenticated,
        HasRoleOrSuper("manager"),
        DjangoModelPermissions,
    ]

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

        start_date_aware = timezone.make_aware(
            datetime.fromisoformat(start_date)
        )
        is_include_archive_date = start_date_aware < (
            timezone.now()
            - timezone.timedelta(days=DAYS_TO_MOVE_VEHICLE_GPS_TO_ARCHIVE)
        )
        if is_include_archive_date and output_format == "geojson":
            archived_points = VehicleGPSPointArchive.objects.filter(
                vehicle_id=vehicle_id,
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
            )
            data["features"].extend(
                GeoJSONGPSPointArchiveSerializer(
                    archived_points, many=True
                ).data["features"]
            )
        elif is_include_archive_date:
            archived_points = VehicleGPSPointArchive.objects.filter(
                vehicle_id=vehicle_id,
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
            )
            archive_vehicle_gps_point_serializer = (
                VehicleGPSPointArchiveSerializer(archived_points, many=True)
            )
            data += archive_vehicle_gps_point_serializer.data

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
        query_archived_points = VehicleGPSPointArchive.objects.none()
        for trip in trips:

            query_current_points = (
                query_current_points
                | VehicleGPSPoint.objects.filter(
                    vehicle_id=vehicle_id,
                    created_at__gte=trip.start_time,
                    created_at__lte=trip.end_time,
                )
            )

            query_archived_points = (
                query_archived_points
                | VehicleGPSPointArchive.objects.filter(
                    vehicle_id=vehicle_id,
                    created_at__gte=trip.start_time,
                    created_at__lte=trip.end_time,
                )
            )

        query_all_tracks_points = query_current_points.union(
            query_archived_points
        ).order_by("created_at")

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
        import_format = request.POST.get("import_format", "csv")
        update_existing = request.POST.get("update_existing") == "on"

        try:
            if import_format == "csv":
                data = self.parse_csv(import_file)
            else:  # json
                data = self.parse_json(import_file)

            results = self.process_data(data, update_existing, request)

            if results["success"]:
                messages.success(request, results["message"])
                context["message_type"] = "success"
            else:
                messages.error(request, results["message"])
                context["message_type"] = "danger"
            # return HttpResponseRedirect(self.success_url)
            context["result_message"] = results["message"]
            return render(request, self.template_name, context)

        except Exception as e:
            error_message = f"Ошибка при импорте данных: {str(e)}"
            messages.error(request, error_message)
            context["result_message"] = error_message
            context["message_type"] = "danger"
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

    def process_data(self, data, update_existing, request):
        raise NotImplementedError(
            "Subclasses must implement process_data method"
        )


class ImportEnterpriseView(ImportView):
    template_name = "enterprises/enterprises_import.html"
    success_url = reverse_lazy("enterprises_list")
    # permission_required = ["vehicle_accounting.add_enterprise"]

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
                enterprise_id = row.get("id")
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
                exists = Enterprise.objects.filter(id=enterprise_id).exists()

                if exists and update_existing:
                    enterprise = Enterprise.objects.get(id=enterprise_id)
                    enterprise.name = name
                    enterprise.city = city
                    enterprise.phone = phone
                    enterprise.email = email
                    enterprise.website = website
                    enterprise.timezone = timezone_str
                    enterprise.save()
                    updated_count += 1
                elif not exists:
                    Enterprise.objects.create(
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
            "message": f"Импорт завершен. Создано: {created_count}, Обновлено: {updated_count}, Ошибок: {error_count}",
        }

        if errors:
            result["message"] += "\n\nОшибки:\n" + "\n".join(errors)

        return result


class ImportVehicleView(ImportView):
    template_name = "vehicles/vehicles_import.html"
    success_url = reverse_lazy("vehicles_list")
    # permission_required = ["vehicle_accounting.add_vehicle"]

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
                car_number = row.get("car_number")
                price = row.get("price")
                year_of_manufacture = row.get("year_of_manufacture")
                mileage = row.get("mileage")
                brand_id = row.get("brand")
                enterprise_id = row.get("enterprise")

                # Необязательные поля
                description = row.get("description", "")
                purchase_datetime_str = row.get("purchase_datetime")
                purchase_datetime = None

                if purchase_datetime_str:
                    purchase_datetime = datetime.datetime.fromisoformat(
                        purchase_datetime_str.replace("Z", "+00:00")
                    )

                # Проверка обязательных полей
                if not all(
                    [
                        car_number,
                        price,
                        year_of_manufacture,
                        mileage,
                        brand_id,
                        enterprise_id,
                    ]
                ):
                    error_count += 1
                    errors.append(
                        f"Отсутствуют обязательные поля для машины: {row}"
                    )
                    continue

                try:
                    enterprise = Enterprise.objects.get(id=enterprise_id)
                except Enterprise.DoesNotExist:
                    error_count += 1
                    errors.append(f"Предприятие '{enterprise_id}' не найдено")
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
                    brand = Brand.objects.get(id=brand_id)
                except Brand.DoesNotExist:
                    error_count += 1
                    errors.append(
                        f"Бренд '{brand_id}' не найден для машины: {car_number}"
                    )
                    continue

                # Проверка существования машины
                exists = Vehicle.objects.filter(car_number=car_number).exists()

                if exists and update_existing:
                    vehicle = Vehicle.objects.get(car_number=car_number)
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

                # Обязательные поля
                start_time_str = row.get("start_time")
                end_time_str = row.get("end_time")

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
                if start_time >= end_time:
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
                trip_id = row.get("id")
                existing_trip = None

                if trip_id:
                    try:
                        existing_trip = Trip.objects.filter(id=trip_id).first()
                    except (Trip.DoesNotExist, ValueError):
                        pass

                if not existing_trip:
                    # Проверяем по автомобилю и времени
                    existing_trip = Trip.objects.filter(
                        vehicle=vehicle,
                        start_time=start_time,
                        end_time=end_time,
                    ).first()

                if existing_trip and update_existing:
                    existing_trip.start_point = start_point
                    existing_trip.end_point = end_point
                    existing_trip.save()
                    updated_count += 1
                elif not existing_trip:
                    Trip.objects.create(
                        vehicle=vehicle,
                        start_time=start_time,
                        end_time=end_time,
                        start_point=start_point,
                        end_point=end_point,
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
