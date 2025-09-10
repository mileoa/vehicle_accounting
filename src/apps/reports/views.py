from datetime import datetime, timedelta

from django.shortcuts import HttpResponseRedirect, get_object_or_404
from django.urls import reverse
from django.views.generic import TemplateView

from apps.enterprises.models import Enterprise
from apps.reports.mixins import WebReportsMixin
from apps.reports.services import (
    BaseReport,
    DriverAssignmentReport,
    VehicleMileageReport,
    VehicleSalesReport,
)
from apps.vehicles.models import Brand, Vehicle


class ReportListView(WebReportsMixin, TemplateView):
    template_name = "reports/report_list.html"
    permission_required = [
        "vehicles.view_vehicle",
        "vehicles.view_driver",
        "vehicles.view_brand",
        "enterprises.view_enterprise",
        "tracking.view_trip",
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

        url = reverse(f"reports:report_{report_type}")
        param_string = "&".join([f"{k}={v}" for k, v in url_params.items()])

        return HttpResponseRedirect(f"{url}?{param_string}")


class VehicleMileageReportView(WebReportsMixin, TemplateView):
    permission_required = [
        "vehicles.view_vehicle",
        "tracking.view_trip",
    ]
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


class VehicleSalesReportView(WebReportsMixin, TemplateView):
    permission_required = [
        "vehicles.view_vehicle",
        "vehicles.view_brand",
        "enterprises.view_enterprise",
    ]
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


class DriverAssignmentReportView(WebReportsMixin, TemplateView):
    permission_required = [
        "vehicles.view_vehicle",
        "vehicles.view_driver",
        "enterprises.view_enterprise",
    ]

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
