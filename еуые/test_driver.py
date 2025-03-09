from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from vehicle_accounting.models import (
    Enterprise,
    Driver,
    Brand,
    Vehicle,
    VehicleDriver,
)


class DriverTestCase(TestCase):
    def setUp(self):
        self.enterprise = Enterprise.objects.create(
            name="ABC Company",
            city="New York",
            phone="123-456-7890",
            email="info@abccompany.com",
        )

    def test_driver_creation(self):
        response = self.client.post(
            reverse("drivers-list"),
            {
                "name": "test_driver_creation",
                "salary": "50000.00",
                "experience_years": "5",
                "enterprise": self.enterprise.pk,
            },
        )

        self.assertEqual(response.status_code, 201, response.content)

        self.assertEqual(
            Driver.objects.filter(name="test_driver_creation").count(), 1
        )

    def test_driver_cannot_change_enterprise_with_assigned_vehicle(self):
        driver = Driver.objects.create(
            name="cannot_change",
            salary=50000.00,
            experience_years=5,
            enterprise=self.enterprise,
        )

        vehicle = Vehicle.objects.create(
            price=30000.00,
            year_of_manufacture=2020,
            mileage=10000,
            car_number="ABC123",
            brand=Brand.objects.create(
                name="Toyota",
                vehicle_type="sedan",
                fuel_tank_capacity_liters=50,
                load_capacity_kg=1000,
                seats_number=5,
            ),
            enterprise=self.enterprise,
        )
        VehicleDriver.objects.create(
            vehicle=vehicle, driver=driver, is_active=True
        )

        new_enterprise = Enterprise.objects.create(
            name="XYZ Company",
            city="Los Angeles",
            phone="987-654-3210",
            email="info@xyzcompany.com",
        )
        driver.enterprise = new_enterprise
        with self.assertRaises(ValidationError):
            driver.save()
