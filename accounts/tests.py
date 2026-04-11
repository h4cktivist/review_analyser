from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


class ProfileViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.profile_url = reverse("profile")

    def test_profile_unauthenticated_returns_401(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_returns_user_data(self):
        reg_url = reverse("register")
        user_data = {
            "email": "profile@example.com",
            "username": "profileuser",
            "password": "TestPassword123!",
            "password2": "TestPassword123!",
            "first_name": "P",
            "last_name": "U",
        }
        reg = self.client.post(reg_url, user_data)
        self.assertEqual(reg.status_code, status.HTTP_201_CREATED)
        access = reg.data["access"]
        response = self.client.get(
            self.profile_url,
            HTTP_AUTHORIZATION=f"Bearer {access}",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "profileuser")
        self.assertEqual(response.data["email"], "profile@example.com")

    def test_me_returns_same_as_profile(self):
        reg_url = reverse("register")
        user_data = {
            "email": "me@example.com",
            "username": "meuser",
            "password": "TestPassword123!",
            "password2": "TestPassword123!",
            "first_name": "M",
            "last_name": "E",
        }
        reg = self.client.post(reg_url, user_data)
        self.assertEqual(reg.status_code, status.HTTP_201_CREATED)
        access = reg.data["access"]
        me_url = reverse("me")
        response = self.client.get(me_url, HTTP_AUTHORIZATION=f"Bearer {access}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "meuser")


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

    def test_registration_rejects_weak_password(self):
        data = self.user_data.copy()
        data["password"] = "123"
        data["password2"] = "123"
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_fields_returns_400(self):
        response = self.client.post(self.login_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
