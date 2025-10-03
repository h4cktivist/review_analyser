import datetime

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

from .models import Institution, Event, Review


User = get_user_model()


class InstitutionCRUDTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

        self.client.force_authenticate(user=self.user)

        self.institution_data = {
            "name": "Тестовый театр",
            "address": "Тестовая улица, 1",
            "yandex_map_link": "https://yandex.maps.example.com/new",
            "gis_map_link": "https://2gis.maps.example.com/new"
        }
        self.institution = Institution.objects.create(**self.institution_data)
        self.list_url = reverse("institution-list")
        self.detail_url = reverse("institution-detail", kwargs={"pk": self.institution.pk})

    def test_get_institutions_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_institution_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Тестовый театр")

    def test_create_institution(self):
        new_data = {
            "name": "Новый театр",
            "address": "Новая улица, 2",
            "yandex_map_link": "https://yandex.maps.example.com/new",
            "gis_map_link": "https://2gis.maps.example.com/new"
        }
        response = self.client.post(self.list_url, new_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Institution.objects.count(), 2)

    def test_update_institution(self):
        update_data = {
            "name": "Обновленный театр",
            "address": "Обновленная улица, 1",
            "yandex_map_link": "https://yandex.maps.example.com/upd",
            "gis_map_link": "https://2gis.maps.example.com/upd"
        }
        response = self.client.put(self.detail_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.institution.refresh_from_db()
        self.assertEqual(self.institution.name, "Обновленный театр")

    def test_delete_institution(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Institution.objects.count(), 0)

    def test_delete_institution_with_reviews(self):
        Review.objects.create(
            institution=self.institution,
            text="Тестовый отзыв",
            sentiment="positive",
            confidence=0.9,
            keywords=["тест"],
            reviewed_at=datetime.datetime.now().astimezone(datetime.timezone.utc)
        )

        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class EventCRUDTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        self.event_data = {"name": "Тестовое мероприятие", "date": "2025-10-03"}
        self.event = Event.objects.create(**self.event_data)
        self.list_url = reverse("event-list")
        self.detail_url = reverse("event-detail", kwargs={"pk": self.event.pk})

    def test_get_events_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_event(self):
        new_data = {"name": "Новое мероприятие", "date": "2025-10-03"}
        response = self.client.post(self.list_url, new_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Event.objects.count(), 2)

    def test_update_event(self):
        update_data = {"name": "Обновленное мероприятие", "date": "2025-10-10"}
        response = self.client.put(self.detail_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.event.refresh_from_db()
        self.assertEqual(self.event.name, "Обновленное мероприятие")

    def test_delete_event(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Event.objects.count(), 0)


class ReviewCRUDTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        self.institution = Institution.objects.create(
            name="Тестовый театр",
            address="Тестовая улица, 1",
            yandex_map_link="https://yandex.maps.example.com/new",
            gis_map_link="https://2gis.maps.example.com/new"
        )
        self.event = Event.objects.create(
            name="Тестовое мероприятие",
            date=datetime.datetime.now().astimezone(datetime.timezone.utc)
        )

        self.review_data = {
            "institution": self.institution.id,
            "text": "Отличный театр!",
            "reviewed_at": "2025-10-03"
        }
        self.review = Review.objects.create(
            institution=self.institution,
            event=self.event,
            text="Тестовый отзыв",
            sentiment="positive",
            confidence=0.9,
            keywords=["тест"],
            reviewed_at=datetime.datetime.now().astimezone(datetime.timezone.utc)
        )
        self.list_url = reverse("review-list")
        self.detail_url = reverse("review-detail", kwargs={"pk": self.review.pk})

    def test_get_reviews_list(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_review(self):
        response = self.client.post(self.list_url, self.review_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 2)

    def test_create_review_without_institution(self):
        invalid_data = self.review_data.copy()
        invalid_data.pop("institution")
        response = self.client.post(self.list_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_review_invalid_confidence(self):
        invalid_data = self.review_data.copy()
        invalid_data["confidence"] = 1.5
        response = self.client.post(self.list_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_review(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Review.objects.count(), 0)


class AuthenticationRequiredTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.institution = Institution.objects.create(
            name="Тестовый театр",
            address="Тестовая улица, 1",
            yandex_map_link="https://yandex.maps.example.com/new",
            gis_map_link="https://2gis.maps.example.com/new"
        )
        self.list_url = reverse("institution-list")
        self.detail_url = reverse("institution-detail", kwargs={"pk": self.institution.pk})

    def test_unauthenticated_access(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.post(self.list_url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
