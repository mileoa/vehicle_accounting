import pytest
from rest_framework.test import APIClient
from django.test import Client
from django.contrib.auth import get_user_model
from tests.factories import EnterpriseFactory
from vehicle_accounting.models import Manager

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def web_client():
    return Client()


@pytest.fixture
def enterprise():

    return EnterpriseFactory()


@pytest.fixture
def manager_user():
    return User.objects.create_user(username="manager", password="testpass123")


@pytest.fixture
def manager(manager_user, enterprise):
    from vehicle_accounting.models import Manager

    manager = Manager.objects.create(user=manager_user)
    manager.enterprises.add(enterprise)
    # Добавляем разрешения
    from django.contrib.auth.models import Permission

    permissions = Permission.objects.filter(
        content_type__app_label="vehicle_accounting"
    )
    manager_user.user_permissions.set(permissions)
    return manager


@pytest.fixture
def default_objects():
    from vehicle_accounting.models import Enterprise, Brand

    enterprise = Enterprise.objects.create(
        name="noname",
        city="Test City",
        phone="123456789",
        email="test@test.com",
    )
    brand = Brand.objects.create(
        name="noname",
        vehicle_type="sedan",
        fuel_tank_capacity_liters=50,
        load_capacity_kg=1000,
        seats_number=5,
    )
    return enterprise, brand
