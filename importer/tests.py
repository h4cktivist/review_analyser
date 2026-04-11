import datetime

from django.test import TestCase
from django.utils import timezone

from reviews.models import Institution, Review

from .views import save_reviews


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
