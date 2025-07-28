import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from vehicle_accounting.models import Vehicle, Manager
from tests.factories import (
    VehicleFactory,
    EnterpriseFactory,
    BrandFactory,
    TripFactory,
)
from django.contrib.auth.models import Permission

User = get_user_model()


@pytest.mark.django_db
class TestVehicleViews:

    def test_vehicle_list_unauthenticated(self, web_client):
        """Неавторизованный доступ к списку автомобилей"""
        url = reverse("vehicles_list")
        response = web_client.get(url)

        assert response.status_code == 302
        assert "login" in response.url

    def test_vehicle_list_authenticated(self, web_client):
        """Авторизованный доступ к списку автомобилей"""
        user = User.objects.create_superuser(
            "admin", "admin@test.com", "testpass123"
        )
        web_client.force_login(user)

        url = reverse("vehicles_list")
        response = web_client.get(url)

        assert response.status_code == 200
        assert "Автомобили" in response.content.decode()

    def test_vehicle_list_with_data(self, web_client):
        """Список автомобилей с данными"""
        user = User.objects.create_superuser(
            "admin", "admin@test.com", "testpass123"
        )
        web_client.force_login(user)

        vehicle = VehicleFactory(car_number="TEST12")

        url = reverse("vehicles_list")
        response = web_client.get(url)

        assert response.status_code == 200
        assert "TEST12" in response.content.decode()

    def test_vehicle_create_get(self, web_client):
        """GET запрос к форме создания автомобиля"""
        user = User.objects.create_superuser(
            "admin", "admin@test.com", "testpass123"
        )
        web_client.force_login(user)

        url = reverse("vehicles_create")
        response = web_client.get(url)

        assert response.status_code == 200
        assert "form" in response.context

    def test_vehicle_create_post_success(self, web_client):
        """Успешное создание автомобиля"""
        user = User.objects.create_superuser(
            "admin", "admin@test.com", "testpass123"
        )
        web_client.force_login(user)

        enterprise = EnterpriseFactory()
        brand = BrandFactory()

        url = reverse("vehicles_create")
        data = {
            "car_number": "NEW123",
            "price": "50000.00",
            "year_of_manufacture": 2023,
            "mileage": 100,
            "description": "Test vehicle",
            "brand": brand.id,
            "enterprise": enterprise.id,
            "purchase_datetime": "2023-01-01 00:00:00",
        }

        response = web_client.post(url, data)

        assert response.status_code == 302
        assert Vehicle.objects.filter(car_number="NEW123").exists()

    def test_vehicle_create_post_invalid(self, web_client):
        """Создание автомобиля с невалидными данными"""
        user = User.objects.create_superuser(
            "admin", "admin@test.com", "testpass123"
        )
        web_client.force_login(user)

        url = reverse("vehicles_create")
        data = {
            "car_number": "",  # Обязательное поле
            "price": "invalid_price",
        }

        response = web_client.post(url, data)

        assert response.status_code == 200  # Остается на форме
        assert "form" in response.context
        assert response.context["form"].errors

    def test_vehicle_detail_view(self, web_client):
        """Просмотр деталей автомобиля"""
        user = User.objects.create_superuser(
            "admin", "admin@test.com", "testpass123"
        )
        web_client.force_login(user)

        vehicle = VehicleFactory(car_number="DETA12")

        url = reverse("vehicle_detail", kwargs={"pk": vehicle.pk})
        response = web_client.get(url)

        assert response.status_code == 200
        assert "DETA12" in response.content.decode()
        assert response.context["vehicle"] == vehicle

    def test_vehicle_update_get(self, web_client):
        """GET запрос к форме редактирования"""
        user = User.objects.create_superuser(
            "admin", "admin@test.com", "testpass123"
        )
        web_client.force_login(user)

        vehicle = VehicleFactory()

        url = reverse("vehicles_update", kwargs={"pk": vehicle.pk})
        response = web_client.get(url)

        assert response.status_code == 200
        assert "form" in response.context

    def test_vehicle_update_post(self, web_client):
        """Редактирование автомобиля"""
        user = User.objects.create_superuser(
            "admin", "admin@test.com", "testpass123"
        )
        web_client.force_login(user)

        vehicle = VehicleFactory(car_number="OLD123")

        url = reverse("vehicles_update", kwargs={"pk": vehicle.pk})
        data = {
            "car_number": "UPD123",
            "price": str(vehicle.price),
            "year_of_manufacture": vehicle.year_of_manufacture,
            "mileage": vehicle.mileage,
            "description": vehicle.description,
            "brand": vehicle.brand.id,
            "enterprise": vehicle.enterprise.id,
            "purchase_datetime": vehicle.purchase_datetime.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

        response = web_client.post(url, data)

        assert response.status_code == 302
        vehicle.refresh_from_db()
        assert vehicle.car_number == "UPD123"

    def test_vehicle_delete_get(self, web_client):
        """GET запрос к странице удаления"""
        user = User.objects.create_superuser(
            "admin", "admin@test.com", "testpass123"
        )
        web_client.force_login(user)

        vehicle = VehicleFactory()

        url = reverse("vehicles_delete", kwargs={"pk": vehicle.pk})
        response = web_client.get(url)

        assert response.status_code == 200
        assert vehicle.car_number in response.content.decode()

    def test_vehicle_delete_post(self, web_client):
        """Удаление автомобиля"""
        user = User.objects.create_superuser(
            "admin", "admin@test.com", "testpass123"
        )
        web_client.force_login(user)

        vehicle = VehicleFactory()
        vehicle_id = vehicle.pk

        url = reverse("vehicles_delete", kwargs={"pk": vehicle.pk})
        response = web_client.post(url)

        assert response.status_code == 302
        assert not Vehicle.objects.filter(pk=vehicle_id).exists()


@pytest.mark.django_db
class TestEnterpriseViews:

    def test_enterprise_list(self, web_client):
        """Список предприятий"""
        user = User.objects.create_superuser(
            "admin", "admin@test.com", "testpass123"
        )
        web_client.force_login(user)

        enterprise = EnterpriseFactory(name="Test Enterprise")

        url = reverse("enterprises_list")
        response = web_client.get(url)

        assert response.status_code == 200
        assert "Test Enterprise" in response.content.decode()

    def test_enterprise_vehicles_list(self, web_client):
        """Список автомобилей предприятия"""
        user = User.objects.create_superuser(
            "admin", "admin@test.com", "testpass123"
        )
        web_client.force_login(user)

        enterprise = EnterpriseFactory()
        vehicle = VehicleFactory(enterprise=enterprise, car_number="ENT123")

        url = reverse("enterprise_vehicles_list", kwargs={"pk": enterprise.pk})
        response = web_client.get(url)

        assert response.status_code == 200
        assert "ENT123" in response.content.decode()
        assert response.context["enterprise"] == enterprise


@pytest.mark.django_db
class TestManagerPermissions:

    def test_manager_access_own_enterprise_vehicles(self, web_client):
        """Менеджер видит автомобили своего предприятия"""
        user = User.objects.create_user(
            "manager", "manager@test.com", "testpass123"
        )
        enterprise = EnterpriseFactory()
        manager = Manager.objects.create(user=user)
        manager.enterprises.add(enterprise)

        permission = Permission.objects.get(codename="view_vehicle")
        user.user_permissions.add(permission)

        vehicle = VehicleFactory(enterprise=enterprise, car_number="MGR123")

        web_client.force_login(user)

        url = reverse("vehicles_list")
        response = web_client.get(url)

        assert response.status_code == 200
        assert "MGR123" in response.content.decode()

    def test_manager_cannot_see_other_enterprise_vehicles(self, web_client):
        """Менеджер не видит автомобили других предприятий"""
        user = User.objects.create_user(
            "manager", "manager@test.com", "testpass123"
        )
        own_enterprise = EnterpriseFactory()
        other_enterprise = EnterpriseFactory()

        manager = Manager.objects.create(user=user)
        manager.enterprises.add(own_enterprise)

        permission = Permission.objects.get(codename="view_vehicle")
        user.user_permissions.add(permission)

        own_vehicle = VehicleFactory(
            enterprise=own_enterprise, car_number="OWN123"
        )
        other_vehicle = VehicleFactory(
            enterprise=other_enterprise, car_number="OTH123"
        )

        web_client.force_login(user)

        url = reverse("vehicles_list")
        response = web_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "OWN123" in content
        assert "OTH123" not in content

    def test_manager_cannot_access_other_enterprise_vehicle_detail(
        self, web_client
    ):
        """Менеджер не может просматривать детали чужих автомобилей"""
        user = User.objects.create_user(
            "manager", "manager@test.com", "testpass123"
        )
        own_enterprise = EnterpriseFactory()
        other_enterprise = EnterpriseFactory()

        manager = Manager.objects.create(user=user)
        manager.enterprises.add(own_enterprise)

        other_vehicle = VehicleFactory(enterprise=other_enterprise)

        web_client.force_login(user)

        url = reverse("vehicle_detail", kwargs={"pk": other_vehicle.pk})
        response = web_client.get(url)

        assert response.status_code == 403


@pytest.mark.django_db
class TestExportViews:

    def test_vehicle_export_csv(self, web_client):
        """Экспорт автомобилей в CSV"""
        user = User.objects.create_superuser(
            "admin", "admin@test.com", "testpass123"
        )
        web_client.force_login(user)

        vehicle = VehicleFactory(car_number="EXP123")

        url = reverse("vehicles_export")
        response = web_client.get(url)

        assert response.status_code == 200
        assert response["Content-Type"] == "csv"
        assert "EXP123" in response.content.decode()

    def test_vehicle_export_json(self, web_client):
        """Экспорт автомобилей в JSON"""
        user = User.objects.create_superuser(
            "admin", "admin@test.com", "testpass123"
        )
        web_client.force_login(user)

        vehicle = VehicleFactory()

        url = reverse("vehicles_export") + "?export_format=json"
        response = web_client.get(url)

        assert response.status_code == 200
        assert response["Content-Type"] == "json"

    def test_enterprise_export(self, web_client):
        """Экспорт предприятия"""
        user = User.objects.create_superuser(
            "admin", "admin@test.com", "testpass123"
        )
        web_client.force_login(user)

        enterprise = EnterpriseFactory()

        url = reverse("enterprises_export", kwargs={"pk": enterprise.pk})
        response = web_client.get(url)

        assert response.status_code == 200
        assert response["Content-Type"] == "csv"


@pytest.mark.django_db
class TestTripMapView:

    def test_trip_map_post(self, web_client):
        """Построение карты поездок"""
        user = User.objects.create_superuser(
            "admin", "admin@test.com", "testpass123"
        )
        web_client.force_login(user)

        trip = TripFactory()

        url = reverse("trip_map")
        data = {"selected_trips": [trip.id]}

        response = web_client.post(url, data)

        assert response.status_code == 201
        assert "map_html" in response.context

    def test_trip_map_no_trips_selected(self, web_client):
        """Карта без выбранных поездок"""
        user = User.objects.create_superuser(
            "admin", "admin@test.com", "testpass123"
        )
        web_client.force_login(user)

        url = reverse("trip_map")
        data = {}

        response = web_client.post(url, data)

        assert response.status_code == 302  # Redirect back


@pytest.mark.django_db
class TestFormValidation:

    def test_vehicle_form_car_number_unique(self, web_client):
        """Проверка уникальности номера автомобиля"""
        user = User.objects.create_superuser(
            "admin", "admin@test.com", "testpass123"
        )
        web_client.force_login(user)

        existing_vehicle = VehicleFactory(car_number="UNI123")
        enterprise = EnterpriseFactory()
        brand = BrandFactory()

        url = reverse("vehicles_create")
        data = {
            "car_number": "UNI123",  # Дублирующийся номер
            "price": "50000.00",
            "year_of_manufacture": 2023,
            "mileage": 100,
            "description": "Test vehicle",
            "brand": brand.id,
            "enterprise": enterprise.id,
            "purchase_datetime": "2023-01-01 00:00:00",
        }

        response = web_client.post(url, data)

        assert response.status_code == 200  # Остается на форме
        assert response.context["form"].errors
        # Проверяем, что второй автомобиль не создался
        assert Vehicle.objects.filter(car_number="UNI123").count() == 1
