from django.apps import AppConfig


class VehilceAccountingAppConfig(AppConfig):
    name = "vehicle_accounting"

    def ready(self):
        import vehicle_accounting.signals
