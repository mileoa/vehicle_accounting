import colorsys
import uuid
from datetime import datetime

import folium
import pytz
from django.contrib import messages
from django.contrib.gis.geos import Point
from django.http import HttpResponse
from django.shortcuts import HttpResponseRedirect, get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views.generic import View
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers as rest_serializers
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from apps.accounts.models import Manager
from apps.importer_exporter.views import ImportView
from apps.tracking.admin import TripResource
from apps.tracking.mixins import WebTripMixin
from apps.tracking.models import Trip, VehicleGPSPoint
from apps.tracking.serializers import (
    GeoJSONVehicleGPSPointSerializer,
    TripSerializer,
    VehicleGPSPointSerializer,
)
from apps.vehicles.models import Vehicle
from core.permissions import HasRoleOrSuper
from core.utils.time import str_iso_datetime_to_timezone


class ExportTrips(WebTripMixin, View):
    model = Trip
    permission_required = [
        "tracking.view_trip",
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


class TripMapView(WebTripMixin, View):
    http_method_names = ["post"]
    permission_required = ["tracking.view_trip"]

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
            "trips/trip_map.html",
            {"map_html": map_html, "selected_trips": selected_trips},
        )


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

    @swagger_auto_schema(
        operation_description="Получить GPS точки поездок для указанного транспортного средства",
        manual_parameters=[
            openapi.Parameter(
                "vehicle_id",
                openapi.IN_QUERY,
                description="ID транспортного средства",
                type=openapi.TYPE_INTEGER,
                required=True,
            ),
            openapi.Parameter(
                "start_date",
                openapi.IN_QUERY,
                description="Дата начала в формате ISO (YYYY-MM-DDTHH:MM:SS)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
                required=True,
            ),
            openapi.Parameter(
                "end_date",
                openapi.IN_QUERY,
                description="Дата окончания в формате ISO (YYYY-MM-DDTHH:MM:SS)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
                required=True,
            ),
            openapi.Parameter(
                "output_format",
                openapi.IN_QUERY,
                description="Формат вывода данных",
                type=openapi.TYPE_STRING,
                enum=["json", "geojson"],
                default="json",
            ),
        ],
        responses={
            200: openapi.Response(
                description="Успешный ответ",
                examples={
                    "application/json": {
                        "json_fromat": [
                            {
                                "id": 1,
                                "latitude": 55.7558,
                                "longitude": 37.6176,
                                "created_at": "2023-01-01T12:00:00Z",
                            }
                        ],
                        "geojson_fromat": {
                            "type": "FeatureCollection",
                            "features": [
                                {
                                    "type": "Feature",
                                    "geometry": {
                                        "type": "Point",
                                        "coordinates": [37.6176, 55.7558],
                                    },
                                    "properties": {
                                        "id": 1,
                                        "created_at": "2023-01-01T12:00:00Z",
                                    },
                                }
                            ],
                        },
                    }
                },
            ),
            400: openapi.Response(description="Ошибка валидации"),
            403: openapi.Response(description="Нет доступа"),
            404: openapi.Response(
                description="Транспортное средство не найдено"
            ),
        },
        tags=["tracking"],
    )
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


class ImportTripView(ImportView):
    template_name = "trips/trip_import.html"
    permission_required = ["tracking.add_trip"]

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
            "created_count": created_count,
            "updated_count": updated_count,
            "error_count": error_count,
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
