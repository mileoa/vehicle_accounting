import uuid
from datetime import timezone as dt_timezone

import factory
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.utils import timezone
from faker import Faker

fake = Faker()

from apps.accounts.models import Manager
from apps.enterprises.models import Enterprise
from apps.tracking.models import Trip, VehicleGPSPoint
from apps.vehicles.models import Brand, Driver, Vehicle, VehicleDriver

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@test.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")


class EnterpriseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Enterprise

    name = factory.Faker("company")
    city = factory.Faker("city")
    phone = factory.Faker("phone_number")
    email = factory.Faker("email")
    website = factory.Faker("url")
    timezone = "UTC"
    uuid = factory.LazyFunction(uuid.uuid4)


class BrandFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Brand

    name = factory.Faker("word")
    vehicle_type = factory.Iterator(["sedan", "truck", "bus", "suv"])
    fuel_tank_capacity_liters = factory.Faker("random_int", min=30, max=100)
    load_capacity_kg = factory.Faker("random_int", min=500, max=5000)
    seats_number = factory.Faker("random_int", min=2, max=50)
    uuid = factory.LazyFunction(uuid.uuid4)


class VehicleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Vehicle

    price = factory.Faker(
        "pydecimal", left_digits=8, right_digits=2, positive=True
    )
    year_of_manufacture = factory.Faker("random_int", min=2000, max=2024)
    mileage = factory.Faker("random_int", min=0, max=200000)
    description = factory.Faker("text", max_nb_chars=200)
    car_number = factory.Sequence(lambda n: f"A{n:05d}")
    brand = factory.SubFactory(BrandFactory)
    enterprise = factory.SubFactory(EnterpriseFactory)
    purchase_datetime = factory.Faker(
        "date_time_this_year", tzinfo=dt_timezone.utc
    )
    uuid = factory.LazyFunction(uuid.uuid4)


class DriverFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Driver

    name = factory.Faker("name")
    salary = factory.Faker(
        "pydecimal", left_digits=8, right_digits=2, positive=True
    )
    experience_years = factory.Faker("random_int", min=1, max=40)
    enterprise = factory.SubFactory(EnterpriseFactory)


class ManagerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Manager

    user = factory.SubFactory(UserFactory)

    @factory.post_generation
    def enterprises(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for enterprise in extracted:
                self.enterprises.add(enterprise)


class VehicleDriverFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = VehicleDriver

    vehicle = factory.SubFactory(VehicleFactory)
    driver = factory.SubFactory(DriverFactory)
    is_active = False

    @factory.lazy_attribute
    def driver(self):
        # Убеждаемся, что водитель принадлежит тому же предприятию
        return DriverFactory(enterprise=self.vehicle.enterprise)


class VehicleGPSPointFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = VehicleGPSPoint

    vehicle = factory.SubFactory(VehicleFactory)
    point = factory.LazyFunction(
        lambda: Point(float(fake.longitude()), float(fake.latitude()))
    )
    created_at = factory.Faker("date_time_this_year", tzinfo=dt_timezone.utc)
    uuid = factory.LazyFunction(uuid.uuid4)


class TripFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Trip

    vehicle = factory.SubFactory(VehicleFactory)
    start_time = factory.Faker("date_time_this_year", tzinfo=dt_timezone.utc)
    end_time = factory.LazyAttribute(
        lambda obj: obj.start_time
        + timezone.timedelta(hours=fake.random_int(min=1, max=8))
    )
    uuid = factory.LazyFunction(uuid.uuid4)

    @factory.post_generation
    def create_gps_points(self, create, extracted, **kwargs):
        if not create:
            return

        # Создаем GPS точки после создания Trip
        self.start_point = VehicleGPSPointFactory(vehicle=self.vehicle)
        self.end_point = VehicleGPSPointFactory(vehicle=self.vehicle)
        self.save()
