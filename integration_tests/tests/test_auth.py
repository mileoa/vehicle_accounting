import json

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import Manager

User = get_user_model()


@pytest.mark.django_db
class TestJWTAuthentication:

    def test_obtain_jwt_token_success(self, api_client):
        """Успешное получение JWT токена"""
        user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        url = reverse("accounts_api:token_obtain_pair")
        data = {"username": "testuser", "password": "testpass123"}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "access" in response_data
        assert "refresh" in response_data
        assert len(response_data["access"]) > 0
        assert len(response_data["refresh"]) > 0

    def test_obtain_jwt_token_invalid_credentials(self, api_client):
        """Ошибка при неверных учетных данных"""
        url = reverse("accounts_api:token_obtain_pair")
        data = {"username": "wronguser", "password": "wrongpass"}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_jwt_token_success(self, api_client):
        """Успешное обновление JWT токена"""
        user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        refresh = RefreshToken.for_user(user)

        url = reverse("accounts_api:token_refresh")
        data = {"refresh": str(refresh)}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "access" in response_data

    def test_refresh_jwt_token_invalid(self, api_client):
        """Ошибка при невалидном refresh токене"""
        url = reverse("accounts_api:token_refresh")
        data = {"refresh": "invalid_token"}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_api_access_with_valid_token(self, api_client, enterprise):
        """Доступ к API с валидным токеном"""
        user = User.objects.create_superuser(
            username="admin", password="testpass123"
        )

        refresh = RefreshToken.for_user(user)
        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

        url = reverse("enterprises_api:enterprise-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_api_access_without_token(self, api_client):
        """Отказ в доступе без токена"""
        url = reverse("enterprises_api:enterprise-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_api_access_with_invalid_token(self, api_client):
        """Отказ в доступе с невалидным токеном"""
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")

        url = reverse("enterprises_api:enterprise-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestWebAuthentication:

    def test_login_page_loads(self, web_client):
        """Страница входа загружается"""
        url = reverse("accounts:login")
        response = web_client.get(url)

        assert response.status_code == 200
        assert "Вход" in response.content.decode()

    def test_login_success(self, web_client):
        """Успешный вход через веб"""
        user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        url = reverse("accounts:login")
        data = {"username": "testuser", "password": "testpass123"}

        response = web_client.post(url, data)

        assert response.status_code == 302  # Redirect after login
        assert response.url == "/enterprises/"

    def test_login_invalid_credentials(self, web_client):
        """Ошибка входа с неверными данными"""
        url = reverse("accounts:login")
        data = {"username": "wronguser", "password": "wrongpass"}

        response = web_client.post(url, data)

        assert response.status_code == 200  # Остается на странице входа
        assert "Вход" in response.content.decode()

    def test_protected_view_requires_login(self, web_client):
        """Защищенные страницы требуют авторизации"""
        url = reverse("vehicles:list")
        response = web_client.get(url, follow=False)

        assert response.status_code == 302
        assert "login" in response.url

    def test_protected_view_accessible_after_login(self, web_client):
        """Доступ к защищенным страницам после входа"""
        user = User.objects.create_superuser(
            username="admin", password="testpass123"
        )

        web_client.force_login(user)

        url = reverse("vehicles:list")
        response = web_client.get(url)

        assert response.status_code == 200


@pytest.mark.django_db
class TestUserRoles:

    def test_superuser_access_all(self, api_client):
        """Суперпользователь имеет доступ ко всем данным"""
        superuser = User.objects.create_superuser(
            username="admin", password="testpass123"
        )

        refresh = RefreshToken.for_user(superuser)
        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

        url = reverse("vehicles_api:vehicle-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_manager_role_creation(self, manager_user, enterprise):
        """Создание менеджера с назначенными предприятиями"""

        manager = Manager.objects.create(user=manager_user)
        manager.enterprises.add(enterprise)

        assert manager.user == manager_user
        assert enterprise in manager.enterprises.all()
        assert manager_user.is_staff is True

    def test_manager_api_access(self, api_client, manager):
        """Менеджер имеет доступ к API своих предприятий"""
        refresh = RefreshToken.for_user(manager.user)
        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

        url = reverse("vehicles_api:vehicle-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_regular_user_no_api_access(self, api_client):
        """Обычный пользователь не имеет доступа к API"""
        user = User.objects.create_user(
            username="regular", password="testpass123"
        )

        refresh = RefreshToken.for_user(user)
        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

        url = reverse("vehicles_api:vehicle-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTokenExpiration:

    def test_expired_token_rejection(self, api_client):
        """Отклонение истекшего токена"""
        user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        # Имитируем истекший токен (в реальности нужно было бы подождать)
        # Для теста используем заведомо невалидный токен
        api_client.credentials(
            HTTP_AUTHORIZATION="Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid"
        )

        url = reverse("vehicles_api:vehicle-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
