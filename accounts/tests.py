from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.token_refresh_url = reverse("refresh")

        self.user_data = {
            "email": "testuser@example.com",
            "username": "testuser",
            "password": "TestPassword123!",
            "password2": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }

    def test_user_registration(self):
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["username"], "testuser")

    def test_user_registration_password_mismatch(self):
        data = self.user_data.copy()
        data["password2"] = "wrongpassword"
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login(self):
        self.client.post(self.register_url, self.user_data)

        login_data = {
            "email": "testuser@example.com",
            "password": "TestPassword123!"
        }
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_user_login_invalid_credentials(self):
        login_data = {
            "email": "wronguser@example.com",
            "password": "wrongpass"
        }
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        reg_response = self.client.post(self.register_url, self.user_data)
        refresh_token = reg_response.data["refresh"]

        # Обновляем токен
        response = self.client.post(self.token_refresh_url, {"refresh": refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_token_refresh_invalid_token(self):
        response = self.client.post(self.token_refresh_url, {"refresh": "invalid_token"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
