from django.test import Client
from rest_framework.test import APIClient
from django.urls import reverse
from vehicle_accounting.models import CustomUser


def test_vehicle_view_with_csrf_protection(self):
    user = CustomUser.objects.create_user(
        "testuser", "test@example.com", "testpassword"
    )

    client = APIClient()
    client.force_authenticate(user=user)

    # Without CSRF token
    response = client.post(reverse("vehicle-list"), data={"field1": "value1"})
    self.assertEqual(response.status_code, 403)

    # With CSRF token
    csrf_token = client.cookies["csrftoken"].value
    client.credentials(HTTP_X_CSRFTOKEN=csrf_token)
    response = client.post(reverse("vehicle-list"), data={"field1": "value1"})
    self.assertEqual(response.status_code, 201)
