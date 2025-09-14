import random
from datetime import datetime, timedelta

import jwt
from locust import FastHttpUser, events, task


class ApiUser(FastHttpUser):
    """
    Пользователь для определения максимального RPS API
    """

    wait_time = lambda self: 0.001  # Минимальная задержка
    weight = 1

    def on_start(self):
        self.jwt_token = None
        self.set_auth_header()
        self.prepare_test_data()

    def set_auth_header(self):
        self.set_jwt_token()
        self.headers = {"Authorization": f"Bearer {self.jwt_token}"}

    def prepare_test_data(self):
        """Подготовка тестовых данных для API запросов"""
        # Получаем актуальные ID для тестов
        self.vehicle_ids = [1]
        self.enterprise_ids = [1]
        self.driver_ids = [1]
        self.brand_ids = [1]

        # Подготавливаем даты для запросов
        self.end_date = datetime.now().date()
        self.start_date = self.end_date - timedelta(days=30)

    def set_jwt_token(self):
        """Получение JWT токена"""
        response = self.client.post(
            "/api/accounts/token/",
            json={"username": "mileoa", "password": "qwer1234"},
        )

        if response.status_code == 200:
            data = response.json()
            self.jwt_token = data["access"]
        else:
            raise Exception(
                f"Не удалось получить токен: {response.status_code}"
            )

    def check_and_refresh_token(self):
        """Проверяет актуальность токена и обновляет при необходимости"""
        current_time = datetime.now().timestamp()
        # Проверяем, истекает ли токен в ближайшие 4 минуты
        if self.token_expires_at - current_time < 60 * 4:
            self.set_auth_header()

    def refresh_jwt_token(self):
        """Обновление JWT токена"""
        response = self.client.post(
            "/api/accounts/token/refresh",
            json={"refresh_token": self.refresh_token},
        )

        if response.status_code == 200:
            self.jwt_token = response.json().get("access_token")
            # Обновляем время истечения
            decoded = jwt.decode(
                self.jwt_token, options={"verify_signature": False}
            )
            self.token_expires_at = decoded.get("exp")
        else:
            # Если refresh токен тоже истек, получаем новый токен
            self.get_jwt_token()

    @task(10)
    def api_vehicles_list(self):
        """Список автомобилей"""
        response = self.client.get(
            "/api/vehicles/", headers=self.headers, name="API: Vehicles List"
        )

    @task(10)
    def api_enterprises_list(self):
        """Список предприятий"""
        response = self.client.get(
            "/api/enterprises/",
            headers=self.headers,
            name="API: Enterprises List",
        )

    @task(1)
    def api_enterprises_detail(self):
        """Детали предприятия"""
        enterprise_id = random.choice(self.enterprise_ids)
        response = self.client.get(
            f"/api/enterprises/{enterprise_id}/",
            headers=self.headers,
            name="API: Enterprise Detail",
        )

    @task(8)
    def api_brands_list(self):
        """Список брендов"""
        response = self.client.get(
            "/api/vehicles/brands/",
            headers=self.headers,
            name="API: Brands List",
        )

    @task(4)
    def api_brands_detail(self):
        """Детали бренда"""
        brand_id = random.choice(self.brand_ids)
        response = self.client.get(
            f"/api/vehicles/brands/{brand_id}/",
            headers=self.headers,
            name="API: Brand Detail",
        )

    @task(8)
    def api_drivers_list(self):
        """Список водителей"""
        response = self.client.get(
            "/api/vehicles/drivers/",
            headers=self.headers,
            name="API: Drivers List",
        )

    @task(6)
    def api_active_drivers(self):
        """Активные водители"""
        response = self.client.get(
            "/api/vehicles/active_drivers/",
            headers=self.headers,
            name="API: Active Drivers",
        )

    @task(8)
    def api_vehicle_gps_points(self):
        """GPS точки автомобиля"""
        vehicle_id = random.choice(self.vehicle_ids)
        params = {
            "vehicle_id": vehicle_id,
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d"),
            "output_format": random.choice(["json", "geojson"]),
        }

        response = self.client.get(
            "/api/tracking/vehicle_gps_points/",
            params=params,
            headers=self.headers,
            name="API: Vehicle GPS Points",
        )

    @task(6)
    def api_trips_tracks(self):
        """Треки поездок"""
        vehicle_id = random.choice(self.vehicle_ids)
        start_datetime = datetime.combine(
            self.start_date, datetime.min.time()
        ).isoformat()
        end_datetime = datetime.combine(
            self.end_date, datetime.min.time()
        ).isoformat()

        params = {
            "vehicle_id": vehicle_id,
            "start_date": start_datetime,
            "end_date": end_datetime,
            "output_format": random.choice(["json", "geojson"]),
        }

        response = self.client.get(
            "/api/tracking/trips_tracks/",
            params=params,
            headers=self.headers,
            name="API: Trips Tracks",
        )

    @task(8)
    def api_trips_list(self):
        """Список поездок"""
        vehicle_id = random.choice(self.vehicle_ids)
        start_datetime = datetime.combine(
            self.start_date, datetime.min.time()
        ).isoformat()
        end_datetime = datetime.combine(
            self.end_date, datetime.min.time()
        ).isoformat()

        params = {
            "vehicle_id": vehicle_id,
            "start_date": start_datetime,
            "end_date": end_datetime,
        }

        response = self.client.get(
            "/api/tracking/trips/",
            params=params,
            headers=self.headers,
            name="API: Trips List",
        )

    @task(1)
    def api_vehicle_mileage_report(self):
        """Отчет по пробегу"""
        vehicle_id = random.choice(self.vehicle_ids)
        period = random.choice(["day", "week", "month", "year"])

        params = {
            "vehicle_id": vehicle_id,
            "period": period,
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d"),
        }

        response = self.client.get(
            "/api/vehicles/vehicle_mileage_report/",
            params=params,
            headers=self.headers,
            name="API: Vehicle Mileage Report",
        )

    @task(3)
    def api_vehicles_paginated(self):
        """Запросы с пагинацией"""
        page = random.randint(1, 5)
        page_size = random.choice([10, 25, 50])

        params = {"page": page, "page_size": page_size}

        response = self.client.get(
            "/api/vehicles/vehicles/",
            params=params,
            headers=self.headers,
            name="API: Vehicles Paginated",
        )

    @task(3)
    def api_vehicles_ordered(self):
        """Запросы с сортировкой"""
        ordering = random.choice(
            ["id", "-id", "price", "-price", "created_at", "-created_at"]
        )

        params = {"ordering": ordering}

        response = self.client.get(
            "/api/vehicles/vehicles/",
            params=params,
            headers=self.headers,
            name="API: Vehicles Ordered",
        )


# Класс для тестирования веб-интерфейса
class WebInterfaceUser(FastHttpUser):
    """
    Пользователь для тестирования веб-интерфейса
    """

    wait_time = lambda self: 0.1
    weight = 2

    def prepare_test_data(self):
        """Подготовка тестовых данных для API запросов"""
        # Получаем актуальные ID для тестов
        self.vehicle_ids = [1]
        self.enterprise_ids = [1]
        self.driver_ids = [1]
        self.brand_ids = [1]

        # Подготавливаем даты для запросов
        self.end_date = datetime.now().date()
        self.start_date = self.end_date - timedelta(days=30)

    def on_start(self):
        self.login()
        self.prepare_test_data()

    def login(self):
        """Авторизация в веб-интерфейсе"""
        try:
            # Получаем страницу логина
            response = self.client.get("/accounts/login/")

            if response.status_code != 200:
                print(
                    f"Ошибка получения страницы логина: {response.status_code}"
                )
                return

            # Извлекаем CSRF токен
            csrf_token = None
            if "csrfmiddlewaretoken" in response.text:
                import re

                csrf_match = re.search(
                    r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text
                )
                if csrf_match:
                    csrf_token = csrf_match.group(1)

            # Данные для авторизации
            login_data = {"username": "mileoa", "password": "qwer1234"}

            if csrf_token:
                login_data["csrfmiddlewaretoken"] = csrf_token

            # Авторизуемся
            login_response = self.client.post(
                "/accounts/login/", data=login_data
            )

        except Exception as e:
            print(f"Исключение при веб-авторизации: {e}")

    @task(1)
    def web_vehicles_list(self):
        """Просмотр списка автомобилей"""
        response = self.client.get("/vehicles/", name="Web: Vehicles List")

    @task(3)
    def web_enterprises_list(self):
        """Просмотр списка предприятий"""
        response = self.client.get(
            "/enterprises/", name="Web: Enterprises List"
        )

    @task(2)
    def web_vehicle_detail(self):
        """Просмотр детальной информации об автомобиле"""
        vehicle_id = random.choice(self.vehicle_ids)
        response = self.client.get(
            f"/vehicles/{vehicle_id}/", name="Web: Vehicle Detail"
        )

    @task(1)
    def web_vehicle_create(self):
        """Страница создания автомобиля"""
        response = self.client.get(
            "/vehicles/create/", name="Web: Vehicle Create"
        )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Начало тестирования"""
    pass


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Окончание тестирования"""
    pass


if __name__ == "__main__":
    print("Команды для определения максимального RPS:")
    print("")

    print(
        "   locust -f locust_max_rps.py --host=http://localhost:8000 -u 100 -r 20 -t 60s --headless"
    )
    print("")
    print("Параметры:")
    print("  -u: количество пользователей (больше = выше RPS)")
    print("  -r: скорость создания пользователей")
    print("  -t: время теста")
    print("  --headless: без веб-интерфейса")
