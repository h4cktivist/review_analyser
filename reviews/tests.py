import datetime

from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

from .models import Institution, Event, Review, SuggestedActionWord


User = get_user_model()


def _review_defaults(institution, **kwargs):
    base = {
        "institution": institution,
        "text": "Тестовый отзыв",
        "sentiment": "positive",
        "confidence": 0.9,
        "source": "test",
        "reviewed_at": datetime.datetime.now().astimezone(datetime.timezone.utc),
    }
    base.update(kwargs)
    return base


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
        Review.objects.create(**_review_defaults(self.institution))

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
            "reviewed_at": "2025-10-03",
            "source": "test",
        }
        self.review = Review.objects.create(
            **_review_defaults(
                self.institution,
                event=self.event,
                text="Тестовый отзыв",
            )
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


@override_settings(EVENTS_WORKER_TOKEN="eternal-worker-token")
class EventWorkerTokenAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.events_url = reverse("event-list")
        self.latest_date_url = reverse("event-latest-date")

    def test_create_event_with_worker_token(self):
        payload = {"name": "Worker imported event", "date": "2026-04-01T10:00:00Z"}
        response = self.client.post(
            self.events_url,
            payload,
            format="json",
            HTTP_AUTHORIZATION="Token eternal-worker-token"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Event.objects.count(), 1)

    def test_create_event_without_auth_is_rejected(self):
        payload = {"name": "Unauthorized event", "date": "2026-04-01T10:00:00Z"}
        response = self.client.post(self.events_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_latest_event_date_with_worker_token(self):
        Event.objects.create(name="Existing event", date="2026-04-01T10:00:00Z")
        response = self.client.get(
            self.latest_date_url,
            HTTP_AUTHORIZATION="Token eternal-worker-token"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["last_event_date"].startswith("2026-04-01T10:00:00"))

    def test_events_with_x_worker_token_header(self):
        payload = {"name": "Header token event", "date": "2026-04-02T12:00:00Z"}
        response = self.client.post(
            self.events_url,
            payload,
            format="json",
            HTTP_X_WORKER_TOKEN="eternal-worker-token",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_events_with_bearer_worker_token(self):
        payload = {"name": "Bearer event", "date": "2026-04-03T12:00:00Z"}
        response = self.client.post(
            self.events_url,
            payload,
            format="json",
            HTTP_AUTHORIZATION="Bearer eternal-worker-token",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_events_list_with_worker_token(self):
        Event.objects.create(name="Listed event", date="2026-04-01T10:00:00Z")
        response = self.client.get(
            self.events_url,
            HTTP_AUTHORIZATION="Token eternal-worker-token",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


@override_settings(EVENTS_WORKER_TOKEN="eternal-worker-token")
class EventLatestDateEmptyTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_latest_event_date_none_when_no_events(self):
        url = reverse("event-latest-date")
        response = self.client.get(
            url,
            HTTP_AUTHORIZATION="Token eternal-worker-token",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["last_event_date"])


class InstitutionDetailExtraTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="user",
            email="user@example.com",
            password="pass12345",
        )
        self.client.force_authenticate(user=self.user)
        self.institution = Institution.objects.create(
            name="Театр",
            address="Улица 1",
            yandex_map_link="https://yandex.maps.example.com/1",
            gis_map_link="https://2gis.maps.example.com/1",
        )
        self.detail_url = reverse("institution-detail", kwargs={"pk": self.institution.pk})

    def test_institution_detail_not_found(self):
        url = reverse("institution-detail", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_admin_cannot_put_or_delete_institution(self):
        response = self.client.put(
            self.detail_url,
            {
                "name": "Другое имя",
                "address": "Другой адрес",
                "yandex_map_link": "https://yandex.maps.example.com/2",
                "gis_map_link": "https://2gis.maps.example.com/2",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class InstitutionListValidationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user = User.objects.create_user(
            username="u",
            email="u@example.com",
            password="p",
        )
        self.client.force_authenticate(user=user)
        self.list_url = reverse("institution-list")

    def test_create_institution_invalid_returns_400(self):
        response = self.client.post(self.list_url, {"name": ""}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EventDetailExtraTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="evuser",
            email="ev@example.com",
            password="pass12345",
        )
        self.client.force_authenticate(user=self.user)
        self.event = Event.objects.create(name="Событие", date="2026-01-01T12:00:00Z")
        self.detail_url = reverse("event-detail", kwargs={"pk": self.event.pk})

    def test_event_detail_not_found(self):
        url = reverse("event-detail", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_admin_cannot_put_or_delete_event(self):
        response = self.client.put(
            self.detail_url,
            {"name": "Новое имя", "date": "2026-01-02T12:00:00Z"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ReviewDetailExtraTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user = User.objects.create_user(
            username="rvuser",
            email="rv@example.com",
            password="pass12345",
        )
        self.client.force_authenticate(user=user)
        self.institution = Institution.objects.create(
            name="Т",
            address="А",
            yandex_map_link="https://yandex.maps.example.com/x",
            gis_map_link="https://2gis.maps.example.com/x",
        )
        self.review = Review.objects.create(**_review_defaults(self.institution, text="Текст"))
        self.detail_url = reverse("review-detail", kwargs={"pk": self.review.pk})

    def test_review_detail_not_found(self):
        url = reverse("review-detail", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_review(self):
        response = self.client.put(
            self.detail_url,
            {
                "institution": self.institution.id,
                "text": "Обновлённый текст",
                "sentiment": "neutral",
                "confidence": 0.5,
                "source": "test",
                "reviewed_at": "2026-01-15T10:00:00Z",
                "positive_aspects": [],
                "negative_aspects": [],
                "required_actions": [],
                "potential_actions": [],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertEqual(self.review.text, "Обновлённый текст")
        self.assertEqual(self.review.sentiment, "neutral")


class ReviewSearchTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user = User.objects.create_user(
            username="searcher",
            email="s@example.com",
            password="pass",
        )
        self.client.force_authenticate(user=user)
        self.institution = Institution.objects.create(
            name="Т",
            address="А",
            yandex_map_link="https://yandex.maps.example.com/x",
            gis_map_link="https://2gis.maps.example.com/x",
        )
        self.review = Review.objects.create(**_review_defaults(self.institution, text="уникальный запрос"))
        self.url = reverse("review-search")

    def test_empty_query_returns_empty_results(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])
        self.assertEqual(response.data["count"], 0)

    def test_search_returns_serialized_reviews(self):
        response = self.client.get(self.url, {"q": "уникальный"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.review.id)

    def test_search_by_id_returns_review(self):
        response = self.client.get(self.url, {"q": str(self.review.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.review.id)


class ActionConfirmationViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user = User.objects.create_user(
            username="actuser",
            email="act@example.com",
            password="pass12345",
        )
        self.client.force_authenticate(user=user)
        self.institution = Institution.objects.create(
            name="Т",
            address="А",
            yandex_map_link="https://yandex.maps.example.com/x",
            gis_map_link="https://2gis.maps.example.com/x",
        )
        self.review = Review.objects.create(
            **_review_defaults(
                self.institution,
                potential_actions=["позвонить", "написать"],
                required_actions=[],
            )
        )
        self.url = reverse("action-confirm", kwargs={"pk": self.review.pk})

    def test_review_not_found(self):
        url = reverse("action-confirm", kwargs={"pk": 99999})
        response = self.client.post(
            url,
            {"action_word": "позвонить", "accepted": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_missing_fields_returns_400(self):
        response = self.client.post(self.url, {"action_word": "позвонить"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(self.url, {"accepted": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_action_not_in_potential_returns_400(self):
        response = self.client.post(
            self.url,
            {"action_word": "несуществующее", "accepted": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_removes_from_potential_only(self):
        response = self.client.post(
            self.url,
            {"action_word": "написать", "accepted": False},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertNotIn("написать", self.review.potential_actions)
        self.assertNotIn("написать", self.review.required_actions)
        self.assertFalse(SuggestedActionWord.objects.filter(word="написать").exists())

    def test_accept_moves_to_required_and_suggests_word(self):
        response = self.client.post(
            self.url,
            {"action_word": "позвонить", "accepted": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertNotIn("позвонить", self.review.potential_actions)
        self.assertIn("позвонить", self.review.required_actions)
        self.assertTrue(SuggestedActionWord.objects.filter(word="позвонить").exists())
