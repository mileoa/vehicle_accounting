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
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import ProtectedError
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.renderers import JSONRenderer
from rest_framework import serializers as rest_serializers
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
