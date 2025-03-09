from rest_framework.test import APITestCase
from rest_framework.test import APIClient
from django.urls import reverse
from vehicle_accounting.models import Enterprise, CustomUser, Manager


class CSRFTestCase(APITestCase):

    def setUp(self):
        self.enterprise = Enterprise.objects.create(name="Test Enterprise")

        self.username = "testuser"
        self.password = "testpassword"
        self.user = CustomUser.objects.create_user(
            self.username, "test@example.com", self.password
        )
        self.manager = Manager.objects.create(user=self.user)

    def test_create_vehicle_with_valid_csrf(self):

        client = APIClient(enforce_csrf_checks=False)

        client.force_authenticate(user=self.user)
        response = self.client.get(reverse("vehicles-list"))
        self.assertEqual(response.status_code, 201)

        csrf_token = self.client.cookies["csrftoken"].value
        self.client.credentials(HTTP_X_CSRFTOKEN=csrf_token)

        data = {"name": "Test Vehicle", "enterprise": self.enterprise.id}
        response = self.client.post(
            reverse("vehicles-list"), data, format="json"
        )
        self.assertEqual(response.status_code, 201)
