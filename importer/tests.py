import asyncio
import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from reviews.models import Institution, Review

from .views import save_reviews
from .services.vk_importer import VKReviewsParser


class SaveReviewsTests(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(
            name="Импорт",
            address="Адрес",
            yandex_map_link="https://yandex.maps.example.com/1",
            gis_map_link="https://2gis.maps.example.com/1",
        )

    def test_creates_reviews_and_skips_duplicate_text(self):
        dt = timezone.make_aware(datetime.datetime(2026, 1, 1, 12, 0, 0))
        batch = [
            {"text": "Первый", "date": dt},
            {"text": "Второй", "date": dt},
        ]
        created, skipped = save_reviews(
            self.institution,
            batch,
            source="unit-test",
            text_key="text",
            date_key="date",
        )
        self.assertEqual(skipped, 0)
        self.assertEqual(len(created), 2)
        self.assertEqual(Review.objects.filter(institution=self.institution).count(), 2)

        again = [
            {"text": "Первый", "date": dt},
            {"text": "Третий", "date": dt},
        ]
        created2, skipped2 = save_reviews(
            self.institution,
            again,
            source="unit-test",
            text_key="text",
            date_key="date",
        )
        self.assertEqual(skipped2, 1)
        self.assertEqual(len(created2), 1)
        self.assertEqual(Review.objects.filter(institution=self.institution).count(), 3)
        texts = set(
            Review.objects.filter(institution=self.institution).values_list("text", flat=True)
        )
        self.assertEqual(texts, {"Первый", "Второй", "Третий"})

    def test_skips_items_without_required_fields(self):
        dt = timezone.make_aware(datetime.datetime(2026, 1, 1, 12, 0, 0))
        batch = [
            {"text": "Корректный отзыв", "date": dt},
            {"text": "Без даты"},
            {"date": dt},
            {},
        ]

        created, skipped = save_reviews(
            self.institution,
            batch,
            source="unit-test",
            text_key="text",
            date_key="date",
        )

        self.assertEqual(len(created), 1)
        self.assertEqual(skipped, 3)
        self.assertEqual(
            Review.objects.filter(institution=self.institution).count(),
            1,
        )


class VKReviewsImportTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email="vk-import@example.com",
            username="vkimport",
            password="TestPassword123!",
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("import-vk-reviews")
        self.institution = Institution.objects.create(
            name="Импорт VK",
            address="Адрес",
            yandex_map_link="https://yandex.maps.example.com/1",
            gis_map_link="https://2gis.maps.example.com/1",
            vk_link="https://vk.com/example_group",
        )

    def test_returns_400_when_vk_access_token_missing(self):
        response = self.client.post(
            self.url,
            {"institution_id": self.institution.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "vk_access_token is required")

    @patch("importer.views.asyncio.run", return_value=[])
    @patch("importer.views.VKReviewsParser")
    def test_uses_vk_access_token_from_request(self, parser_mock, asyncio_run_mock):
        token = "vk_token_from_frontend"
        response = self.client.post(
            self.url,
            {"institution_id": self.institution.id, "vk_access_token": token},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        parser_mock.assert_called_once_with(
            group_id="example_group",
            token=token,
            from_date=None,
        )
        asyncio_run_mock.assert_called_once()


class VKReviewsParserTests(TestCase):
    @patch("importer.services.vk_importer.VKClient.call")
    def test_skips_comments_without_date(self, call_mock):
        async def side_effect(method, params):
            if method == "utils.resolveScreenName":
                return {"type": "group", "object_id": 123}
            if method == "wall.get":
                if params.get("offset", 0) == 0:
                    return {"items": [{"id": 1, "date": 1_700_000_000, "comments": {"count": 1}}]}
                return {"items": []}
            if method == "wall.getComments":
                if params.get("offset", 0) == 0:
                    return {"items": [{"id": 10, "text": "ok"}, {"id": 11, "text": "has date", "date": 1_700_000_001}]}
                return {"items": []}
            return {"items": []}

        call_mock.side_effect = side_effect
        parser = VKReviewsParser(group_id="group", token="token")
        result = asyncio.run(parser.parse())

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["text"], "has date")

    @patch("importer.services.vk_importer.asyncio.sleep")
    @patch("importer.services.vk_importer.VKClient.call")
    def test_resolve_group_id_called_once_for_multiple_posts(self, call_mock, sleep_mock):
        async def side_effect(method, params):
            if method == "utils.resolveScreenName":
                return {"type": "group", "object_id": 123}
            if method == "wall.get":
                if params.get("offset", 0) == 0:
                    return {
                        "items": [
                            {"id": 1, "date": 1_700_000_000, "comments": {"count": 1}},
                            {"id": 2, "date": 1_700_000_100, "comments": {"count": 1}},
                        ]
                    }
                return {"items": []}
            if method == "wall.getComments":
                return {"items": []}
            return {"items": []}

        call_mock.side_effect = side_effect
        parser = VKReviewsParser(group_id="group", token="token")
        asyncio.run(parser.parse())

        resolve_calls = [
            c for c in call_mock.call_args_list if c.args[0] == "utils.resolveScreenName"
        ]
        self.assertEqual(len(resolve_calls), 1)
        self.assertTrue(sleep_mock.called)
