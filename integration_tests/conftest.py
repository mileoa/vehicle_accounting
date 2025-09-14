import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.test import Client
from rest_framework.test import APIClient

from apps.accounts.models import Manager
from apps.enterprises.models import Enterprise
from apps.vehicles.models import Brand

from .factories import EnterpriseFactory

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

    manager = Manager.objects.create(user=manager_user)
    manager.enterprises.add(enterprise)
    return manager


@pytest.fixture
def default_objects():

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


@pytest.fixture(scope="session", autouse=True)
def setup_test_groups(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("create_managers_group")
