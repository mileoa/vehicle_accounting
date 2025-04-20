from datetime import datetime, timedelta
import pytz
from django.contrib.gis.geos import Point
from django.utils import timezone
from django.db.models import Sum, Count, Avg, F, Q
from django.db.models.functions import (
    TruncDay,
    TruncWeek,
    TruncMonth,
    TruncYear,
)

from .models import (
    Vehicle,
    Brand,
    Enterprise,
    Trip,
    VehicleGPSPoint,
    VehicleGPSPointArchive,
    Driver,
    VehicleDriver,
)


class BaseReport:

    PERIOD_CHOICES = [
        ("day", "День"),
        ("week", "Неделя"),
        ("month", "Месяц"),
        ("year", "Год"),
    ]

    def __init__(self, start_date, end_date, period):
        self.start_date = start_date
        self.end_date = end_date
        self.period = period
        self.title = "Базовый отчет"

    def get_period_format(self):
        if self.period == "day":
            return "%Y-%m-%d"
        if self.period == "week":
            return "%Y-%W"
        if self.period == "month":
            return "%Y-%m"
        if self.period == "year":
            return "%Y"
        return None

    def get_period_key(self, date):
        if self.period == "day":
            return date.strftime("%Y-%m-%d")
        if self.period == "week":
            return date.strftime("%Y-%W")
        if self.period == "month":
            return date.strftime("%Y-%m")
        if self.period == "year":
            return date.strftime("%Y")
        return None

    def get_next_period(self, date):
        if self.period == "day":
            return date + timedelta(days=1)
        if self.period == "week":
            return date + timedelta(days=7)
        if self.period == "month" and date.month == 12:
            return date.replace(year=date.year + 1, month=1, day=1)
        if self.period == "month" and date.month < 12:
            return date.replace(month=date.month + 1, day=1)
        if self.period == "year":
            return date.replace(year=date.year + 1, month=1, day=1)
        return None

    def format_period_label(self, period_key):
        if self.period == "day":
            # Convert YYYY-MM-DD to DD.MM.YYYY
            try:
                dt = datetime.strptime(period_key, "%Y-%m-%d")
                return dt.strftime("%d.%m.%Y")
            except ValueError:
                return period_key
        if self.period == "week":
            # Convert YYYY-WW to "Week WW, YYYY"
            try:
                year, week = period_key.split("-")
                return f"Неделя {week}, {year}"
            except ValueError:
                return period_key
        if self.period == "month":
            # Convert YYYY-MM to "Month YYYY"
            try:
                year, month = period_key.split("-")
                dt = datetime(int(year), int(month), 1)
                return dt.strftime("%B %Y")
            except (ValueError, IndexError):
                return period_key
        if self.period == "year":
            return period_key
        return None

    def calculate_trip_mileage(self, trip):
        # Get GPS points for this trip in order
        gps_points = list(
            VehicleGPSPoint.objects.filter(
                vehicle=trip.vehicle,
                created_at__gte=trip.start_time,
                created_at__lte=trip.end_time,
            ).order_by("created_at")
        )

        # Add archive points if needed
        archive_points = list(
            VehicleGPSPointArchive.objects.filter(
                vehicle=trip.vehicle,
                created_at__gte=trip.start_time,
                created_at__lte=trip.end_time,
            ).order_by("created_at")
        )

        # Combine and sort by created_at
        all_points = sorted(
            gps_points + archive_points, key=lambda p: p.created_at
        )

        # Calculate total distance
        total_distance = 0

        for i in range(1, len(all_points)):
            # Calculate distance between consecutive points
            point1 = all_points[i - 1].point
            point2 = all_points[i].point

            # Calculate distance in meters
            distance = (
                point1.distance(point2) * 100000
            )  # Convert to meters (approximate)
            total_distance += distance

        # Return distance in kilometers
        return total_distance / 1000

    def generate(self):
        raise NotImplementedError("Subclasses must implement this method")


class VehicleMileageReport(BaseReport):

    def __init__(
        self, start_date, end_date, period="day", vehicle=None, enterprise=None
    ):
        super().__init__(start_date, end_date, period)
        self.vehicle = vehicle
        self.enterprise = enterprise
        self.title = "Отчет по пробегу автомобиля"

    def generate(self):
        result = {"title": self.title, "data": {}, "totals": {"mileage_km": 0}}

        # Get vehicles to report on
        vehicles = []
        if self.vehicle:
            vehicles = [self.vehicle]
        elif self.enterprise:
            vehicles = Vehicle.objects.filter(enterprise=self.enterprise)
        else:
            return result  # No vehicles selected

        # Generate report data
        for vehicle in vehicles:
            # Get all trips for the vehicle in the date range
            trips = Trip.objects.filter(
                vehicle=vehicle,
                start_time__date__gte=self.start_date,
                end_time__date__lte=self.end_date,
            ).order_by("start_time")

            vehicle_data = {}

            for trip in trips:
                # Get period key based on format
                period_key = self.get_period_key(trip.start_time.date())

                # Format the label for display
                period_label = self.format_period_label(period_key)

                # Calculate trip mileage from GPS points
                trip_mileage = self.calculate_trip_mileage(trip)

                # Add to result
                if period_key not in vehicle_data:
                    vehicle_data[period_key] = {
                        "label": period_label,
                        "value": 0,
                    }

                vehicle_data[period_key]["value"] += trip_mileage
                result["totals"]["mileage_km"] += trip_mileage

            # Add vehicle data to result
            result["data"][vehicle.car_number] = {
                "name": f"{vehicle.car_number} ({vehicle.brand})",
                "periods": vehicle_data,
                "total": sum(
                    period["value"] for period in vehicle_data.values()
                ),
            }

        return result


class VehicleSalesReport(BaseReport):

    def __init__(
        self, start_date, end_date, period="day", brand=None, enterprise=None
    ):
        super().__init__(start_date, end_date, period)
        self.brand = brand
        self.enterprise = enterprise
        self.title = "Отчет по продажам автомобилей"

    def generate(self):
        result = {"title": self.title, "data": {}}
        vehicles = Vehicle.objects.all()
        vehicles = vehicles.filter(purchase_datetime__date__gte=self.start_date)
        vehicles = vehicles.filter(purchase_datetime__date__lte=self.end_date)

        if self.brand:
            vehicles = vehicles.filter(brand=self.brand)

        if self.enterprise:
            vehicles = vehicles.filter(enterprise=self.enterprise)

        # Group data by period
        period_data = {}
        brand_data = {}
        enterprise_data = {}

        # Process each vehicle
        for vehicle in vehicles:
            if not vehicle.purchase_datetime:
                continue

            # Get period key
            period_key = self.get_period_key(vehicle.purchase_datetime.date())
            period_label = self.format_period_label(period_key)

            # Initialize period data if not exists
            if period_key not in period_data:
                period_data[period_key] = {
                    "label": period_label,
                    "count": 0,
                    "total_amount": 0,
                    "brands": {},
                    "enterprises": {},
                }

            # Initialize brand data if not exists
            brand_name = str(vehicle.brand)
            if brand_name not in brand_data:
                brand_data[brand_name] = {
                    "name": brand_name,
                    "count": 0,
                    "total_amount": 0,
                    "periods": {},
                }

            # Initialize enterprise data if not exists
            enterprise_name = str(vehicle.enterprise)
            if enterprise_name not in enterprise_data:
                enterprise_data[enterprise_name] = {
                    "name": enterprise_name,
                    "count": 0,
                    "total_amount": 0,
                    "periods": {},
                }

            # Initialize period data for brand
            if period_key not in brand_data[brand_name]["periods"]:
                brand_data[brand_name]["periods"][period_key] = {
                    "label": period_label,
                    "count": 0,
                    "total_amount": 0,
                }

            # Initialize period data for enterprise
            if period_key not in enterprise_data[enterprise_name]["periods"]:
                enterprise_data[enterprise_name]["periods"][period_key] = {
                    "label": period_label,
                    "count": 0,
                    "total_amount": 0,
                }

            # Initialize brand data for period
            if brand_name not in period_data[period_key]["brands"]:
                period_data[period_key]["brands"][brand_name] = {
                    "count": 0,
                    "total_amount": 0,
                }

            # Initialize enterprise data for period
            if enterprise_name not in period_data[period_key]["enterprises"]:
                period_data[period_key]["enterprises"][enterprise_name] = {
                    "count": 0,
                    "total_amount": 0,
                }

            # Update period data
            period_data[period_key]["count"] += 1
            period_data[period_key]["total_amount"] += vehicle.price
            period_data[period_key]["brands"][brand_name]["count"] += 1
            period_data[period_key]["brands"][brand_name][
                "total_amount"
            ] += vehicle.price
            period_data[period_key]["enterprises"][enterprise_name][
                "count"
            ] += 1
            period_data[period_key]["enterprises"][enterprise_name][
                "total_amount"
            ] += vehicle.price

            # Update brand data
            brand_data[brand_name]["count"] += 1
            brand_data[brand_name]["total_amount"] += vehicle.price
            brand_data[brand_name]["periods"][period_key]["count"] += 1
            brand_data[brand_name]["periods"][period_key][
                "total_amount"
            ] += vehicle.price

            # Update enterprise data
            enterprise_data[enterprise_name]["count"] += 1
            enterprise_data[enterprise_name]["total_amount"] += vehicle.price
            enterprise_data[enterprise_name]["periods"][period_key][
                "count"
            ] += 1
            enterprise_data[enterprise_name]["periods"][period_key][
                "total_amount"
            ] += vehicle.price

        # Calculate totals
        total_count = sum(period["count"] for period in period_data.values())
        total_amount = sum(
            period["total_amount"] for period in period_data.values()
        )

        # Add all data to result
        result["data"] = {
            "periods": period_data,
            "brands": brand_data,
            "enterprises": enterprise_data,
            "totals": {"count": total_count, "total_amount": total_amount},
        }

        return result


class DriverAssignmentReport(BaseReport):

    def __init__(self, start_date, end_date, period="day", enterprises=None):
        super().__init__(start_date, end_date, period)
        self.enterprises = enterprises or []
        self.title = "Отчет о назначении водителей"

    def generate(self):
        result = {"title": self.title, "data": {}}
        enterprises = self.enterprises

        # Enterprise statistics
        enterprise_stats = {}
        overall_stats = {
            "total_vehicles": 0,
            "total_drivers_count": 0,
            "assigned_drivers_count": 0,
            "unassigned_drivers_count": 0,
            "vehicles_with_drivers": 0,
            "vehicles_without_drivers": 0,
            "driver_vehicle_ratio": 0,
            "assignment_history": {},
        }

        for enterprise in enterprises:
            # Get all drivers and vehicles for this enterprise
            drivers = Driver.objects.filter(enterprise=enterprise)
            vehicles = Vehicle.objects.filter(enterprise=enterprise)

            # Count assigned and unassigned drivers
            assigned_drivers_count = (
                Driver.objects.filter(
                    enterprise=enterprise, driver_vehicles__is_active=True
                )
                .distinct()
                .count()
            )

            total_drivers_count = drivers.count()
            unassigned_drivers_count = (
                total_drivers_count - assigned_drivers_count
            )

            # Count vehicles with and without active drivers
            vehicles_with_drivers = (
                Vehicle.objects.filter(
                    enterprise=enterprise, vehicle_drivers__is_active=True
                )
                .distinct()
                .count()
            )

            total_vehicles = vehicles.count()
            vehicles_without_drivers = total_vehicles - vehicles_with_drivers

            # Calculate driver to vehicle ratio
            driver_vehicle_ratio = (
                round(total_drivers_count / total_vehicles, 2)
                if total_vehicles > 0
                else 0
            )

            # Get assignment history within the date range
            vehicle_drivers = VehicleDriver.objects.filter(
                vehicle__enterprise=enterprise,
                vehicle__created_at__date__gte=self.start_date,
                vehicle__created_at__date__lte=self.end_date,
            ).select_related("driver", "vehicle")

            # Process assignment history by period
            assignment_history = {}

            for vd in vehicle_drivers:
                period_key = self.get_period_key(vd.vehicle.created_at.date())
                period_label = self.format_period_label(period_key)

                if period_key not in assignment_history:
                    assignment_history[period_key] = {
                        "label": period_label,
                        "new_assignments": 0,
                        "active_assignments": 0,
                    }

                assignment_history[period_key]["new_assignments"] += 1
                if vd.is_active:
                    assignment_history[period_key]["active_assignments"] += 1

            # Store enterprise stats
            enterprise_stats[enterprise.name] = {
                "name": enterprise.name,
                "total_vehicles": total_vehicles,
                "total_drivers_count": total_drivers_count,
                "assigned_drivers_count": assigned_drivers_count,
                "unassigned_drivers_count": unassigned_drivers_count,
                "vehicles_with_drivers": vehicles_with_drivers,
                "vehicles_without_drivers": vehicles_without_drivers,
                "driver_vehicle_ratio": driver_vehicle_ratio,
                "assignment_history": assignment_history,
            }

            # Update overall stats
            overall_stats["total_vehicles"] += total_vehicles
            overall_stats["total_drivers_count"] += total_drivers_count
            overall_stats["assigned_drivers_count"] += assigned_drivers_count
            overall_stats[
                "unassigned_drivers_count"
            ] += unassigned_drivers_count
            overall_stats["vehicles_with_drivers"] += vehicles_with_drivers
            overall_stats[
                "vehicles_without_drivers"
            ] += vehicles_without_drivers

            # Merge assignment history
            for period_key, period_data in assignment_history.items():
                if period_key not in overall_stats["assignment_history"]:
                    overall_stats["assignment_history"][period_key] = {
                        "label": period_data["label"],
                        "new_assignments": 0,
                        "active_assignments": 0,
                    }

                overall_stats["assignment_history"][period_key][
                    "new_assignments"
                ] += period_data["new_assignments"]
                overall_stats["assignment_history"][period_key][
                    "active_assignments"
                ] += period_data["active_assignments"]

        # Calculate overall driver to vehicle ratio
        if overall_stats["total_vehicles"] > 0:
            overall_stats["driver_vehicle_ratio"] = round(
                overall_stats["total_drivers_count"]
                / overall_stats["total_vehicles"],
                2,
            )

        # Add all data to result
        result["data"] = {
            "enterprise_stats": enterprise_stats,
            "overall_stats": overall_stats,
        }

        return result
