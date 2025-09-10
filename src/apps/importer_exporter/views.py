import csv
import json
from io import TextIOWrapper

import gpxpy
from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.db import transaction
from django.shortcuts import render
from django.views.generic import View


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
