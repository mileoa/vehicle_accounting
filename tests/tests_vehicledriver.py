from django.test import TestCase
from django.core.exceptions import ValidationError
from vehicle_accounting.models import (
    Brand,
    Enterprise,
    Vehicle,
    Driver,
    VehicleDriver,
)


class VehicleDriverTestCase(TestCase):
    def setUp(self):
        self.enterprise = Enterprise.objects.create(
            name="ABC Company",
            city="New York",
            phone="123-456-7890",
            email="info@abccompany.com",
        )
        self.brand = Brand.objects.create(
            name="Toyota",
            vehicle_type="sedan",
            fuel_tank_capacity_liters=50,
            load_capacity_kg=1000,
            seats_number=5,
        )
        self.vehicle = Vehicle.objects.create(
            price=30000.00,
            year_of_manufacture=2020,
            mileage=10000,
            car_number="ABC123",
            brand=self.brand,
            enterprise=self.enterprise,
        )
        self.driver1 = Driver.objects.create(
            name="John Doe",
            salary=50000.00,
            experience_years=5,
            enterprise=self.enterprise,
        )
        self.driver2 = Driver.objects.create(
            name="Jane Smith",
            salary=55000.00,
            experience_years=7,
            enterprise=self.enterprise,
        )

    def test_vehicle_driver_must_belong_to_same_enterprise(self):
        new_enterprise = Enterprise.objects.create(
            name="XYZ Company",
            city="Los Angeles",
            phone="987-654-3210",
            email="info@xyzcompany.com",
        )
        new_driver = Driver.objects.create(
            name="Jane Smith",
            salary=55000.00,
            experience_years=7,
            enterprise=new_enterprise,
        )
        with self.assertRaises(ValidationError):
            VehicleDriver.objects.create(
                vehicle=self.vehicle, driver=new_driver, is_active=False
            )

    def test_only_one_active_driver_per_vehicle(self):
        VehicleDriver.objects.create(
            vehicle=self.vehicle, driver=self.driver1, is_active=True
        )
        with self.assertRaises(ValidationError):
            VehicleDriver.objects.create(
                vehicle=self.vehicle, driver=self.driver2, is_active=True
            )

    def test_only_one_active_vehicle_per_driver(self):
        other_vehicle = Vehicle.objects.create(
            price=35000.00,
            year_of_manufacture=2021,
            mileage=5000,
            car_number="DEF456",
            brand=self.brand,
            enterprise=self.enterprise,
        )
        VehicleDriver.objects.create(
            vehicle=self.vehicle, driver=self.driver1, is_active=True
        )
        with self.assertRaises(ValidationError):
            VehicleDriver.objects.create(
                vehicle=other_vehicle, driver=self.driver1, is_active=True
            )
