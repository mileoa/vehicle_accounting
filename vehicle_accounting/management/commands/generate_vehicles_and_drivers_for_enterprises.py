import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from faker import Faker
from vehicle_accounting.models import (
    Enterprise,
    Brand,
    Vehicle,
    Driver,
    VehicleDriver,
)


class Command(BaseCommand):
    help = "Генерация тестовых данных для транспортных средств и водителей"

    def add_arguments(self, parser):
        parser.add_argument(
            "enterprise_ids",
            nargs="+",
            type=int,
            help="ID предприятий, для которых генерировать данные",
        )
        parser.add_argument(
            "num_vehicles",
            type=int,
            help="Количество транспортных средств для генерации",
        )
        parser.add_argument(
            "num_drivers", type=int, help="Количество водителей для генерации"
        )

    def handle(self, *args, **options):
        fake = Faker()
        enterprise_ids = options["enterprise_ids"]
        num_vehicles = options["num_vehicles"]
        num_drivers = options["num_drivers"]

        # Получение списка предприятий по указанным ID
        enterprises = list(Enterprise.objects.filter(id__in=enterprise_ids))

        # Создание транспортных средств
        brands = list(Brand.objects.all())
        for _ in range(num_vehicles):
            enterprise = random.choice(enterprises)
            brand = random.choice(brands)
            Vehicle.objects.create(
                price=Decimal(
                    fake.pydecimal(left_digits=8, right_digits=2, positive=True)
                ),
                year_of_manufacture=random.randint(0, 2025),
                mileage=random.randint(0, 200000),
                description=fake.text(),
                car_number=fake.unique.license_plate()[:6],
                brand=brand,
                enterprise=enterprise,
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"Создано {num_vehicles} транспортных средств для {len(enterprises)} предприятий"
            )
        )

        # Создание водителей
        for _ in range(num_drivers):
            enterprise = random.choice(enterprises)
            Driver.objects.create(
                name=fake.name(),
                salary=Decimal(
                    fake.pydecimal(left_digits=8, right_digits=2, positive=True)
                ),
                experience_years=random.randint(1, 100),
                enterprise=enterprise,
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"Создано {num_drivers} водителей для {len(enterprises)} предприятий"
            )
        )

        # Назначение водителей на транспортные средства
        vehicles = list(Vehicle.objects.filter(enterprise__in=enterprises))
        assigned_amount = 0
        for vehicle in vehicles:
            should_assign_driver = random.random() < 0.1
            if not should_assign_driver:
                continue
            have_active_driver = VehicleDriver.objects.filter(
                vehicle=vehicle, is_active=True
            ).exists()
            if have_active_driver:
                continue
            drivers = Driver.objects.filter(enterprise=vehicle.enterprise)
            driver = random.choice(drivers)
            is_active_driver = VehicleDriver.objects.filter(
                driver=driver, is_active=True
            ).exists()
            belong_to_same_enterprise = vehicle.enterprise == driver.enterprise
            if not is_active_driver and belong_to_same_enterprise:
                VehicleDriver.objects.create(
                    vehicle=vehicle, driver=driver, is_active=True
                )
                assigned_amount += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Назначено {assigned_amount} активных водителей"
            )
        )
