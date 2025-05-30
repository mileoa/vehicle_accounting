# Generated by Django 5.1.5 on 2025-04-13 11:26

from django.db import migrations, models
import uuid


def gen_uuid(apps, schema_editor):
    """
    Функция для генерации UUID для существующих записей
    """
    # Получаем модели из состояния миграции
    Enterprise = apps.get_model("vehicle_accounting", "Enterprise")
    Vehicle = apps.get_model("vehicle_accounting", "Vehicle")
    Brand = apps.get_model("vehicle_accounting", "Brand")
    Driver = apps.get_model("vehicle_accounting", "Driver")
    Trip = apps.get_model("vehicle_accounting", "Trip")

    # Генерируем UUID для каждой записи в каждой модели
    for model in [Enterprise, Vehicle, Brand, Driver, Trip]:
        for obj in model.objects.all():
            obj.uuid = uuid.uuid4()
            obj.save()


class Migration(migrations.Migration):

    dependencies = [
        (
            "vehicle_accounting",
            "0013_brand_uuid_enterprise_uuid_trip_uuid_vehicle_uuid_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(gen_uuid),
    ]
