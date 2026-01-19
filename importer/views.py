import asyncio

from django.db.models import Max
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.db import transaction
from django.conf import settings

from reviews.models import Institution, Review
from reviews.serializers import ReviewSerializer
from importer.services.gis_importer import fetch_reviews_with_pagination
from importer.services.yandex_importer import yandex_reviews_importer
from importer.services.telegram_importer import parse_telegram_comments
from importer.services.vk_importer import VKReviewsParser
from importer.services.otzovik_importer import OtzovikReviewsParser
from .tasks import extract_aspects_for_review, compare_review_with_event, classify_review_sentiment, wrap_profanity


def save_reviews(institution, reviews_data, source, text_key, date_key):
    existing_texts = set(
        Review.objects.filter(
            institution=institution
        ).values_list("text", flat=True)
    )

    new_reviews = []
    skipped_count = 0

    for data in reviews_data:
        text = data[text_key]
        if text in existing_texts:
            skipped_count += 1
            continue

        new_reviews.append(
            Review(
                institution=institution,
                text=text,
                source=source,
                reviewed_at=data[date_key],
            )
        )

    with transaction.atomic():
        created_reviews = Review.objects.bulk_create(new_reviews)

    return created_reviews, skipped_count


class BaseReviewsImportView(APIView):
    source_name = None
    text_key = "text"
    date_key = "date"

    def get_institution(self, institution_id):
        try:
            return Institution.objects.get(pk=institution_id)
        except Institution.DoesNotExist:
            return None

    def run_postprocessing(self, reviews):
        for review in reviews:
            compare_review_with_event.delay(review.id)
            classify_review_sentiment.delay(review.id)
            extract_aspects_for_review.delay(review.id)
            wrap_profanity.delay(review.id)

    def response_ok(self, reviews, skipped_count, total_processed):
        serializer = ReviewSerializer(reviews, many=True)
        return Response(
            {
                "message": (
                    f"Successfully imported {len(reviews)} reviews, "
                    f"skipped {skipped_count} duplicates"
                ),
                "imported_reviews": serializer.data,
                "total_processed": total_processed,
            },
            status=status.HTTP_201_CREATED,
        )

    def response_not_found(self):
        return Response(
            {"error": "Institution is not found"},
            status=status.HTTP_404_NOT_FOUND,
        )


class GISReviews(BaseReviewsImportView):
    source_name = "2GIS"
    date_key = "date_created"

    def post(self, request):
        institution = self.get_institution(request.data.get("institution_id"))
        if not institution:
            return self.response_not_found()

        gis_id = int(institution.gis_map_link.split("/")[-1])
        url = (
            f"https://public-api.reviews.2gis.com/3.0/branches/"
            f"{gis_id}/reviews?limit=50&key={settings.GIS_KEY}"
            f"&locale=ru_RU&sort_by=date_created"
        )

        try:
            reviews_data = fetch_reviews_with_pagination(
                initial_url=url,
                auth_header=f"Bearer {settings.GIS_AUTH_TOKEN}",
            )

            created, skipped = save_reviews(
                institution,
                reviews_data,
                source=self.source_name,
                text_key=self.text_key,
                date_key=self.date_key,
            )

            self.run_postprocessing(created)

            return self.response_ok(
                created,
                skipped,
                total_processed=len(reviews_data),
            )

        except Exception as e:
            return Response(
                {"error": f"Error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class YandexReviews(BaseReviewsImportView):
    source_name = "Яндекс Карты"

    def post(self, request):
        institution = self.get_institution(request.data.get("institution_id"))
        if not institution:
            return self.response_not_found()

        yandex_id = int(institution.yandex_map_link.split("/")[-1])

        try:
            data = yandex_reviews_importer.parse_reviews(yandex_id=yandex_id)
            reviews = data["company_reviews"]

            created, skipped = save_reviews(
                institution,
                reviews,
                source=self.source_name,
                text_key=self.text_key,
                date_key=self.date_key,
            )

            self.run_postprocessing(created)

            return self.response_ok(
                created,
                skipped,
                total_processed=len(reviews),
            )

        except Exception as e:
            return Response(
                {"error": f"Error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TelegramReviews(BaseReviewsImportView):
    source_name = "Telegram"

    def post(self, request):
        institution = self.get_institution(request.data.get("institution_id"))
        if not institution:
            return self.response_not_found()

        tg_channel = institution.telegram_link.split("/")[-1]

        last_review_dt = (
            Review.objects.filter(
                institution=institution,
                source=self.source_name,
            )
            .aggregate(last_date=Max("reviewed_at"))
            ["last_date"]
        )

        try:
            reviews = parse_telegram_comments(
                channel_username=tg_channel,
                since_dt=last_review_dt,
            )

            created, skipped = save_reviews(
                institution,
                reviews,
                source=self.source_name,
                text_key="text",
                date_key="date",
            )

            self.run_postprocessing(created)

            return self.response_ok(
                created,
                skipped,
                total_processed=len(reviews),
            )

        except Exception as e:
            return Response(
                {"error": f"Error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VKReviews(BaseReviewsImportView):
    source_name = "VK"

    def post(self, request):
        institution = self.get_institution(request.data.get("institution_id"))
        if not institution:
            return self.response_not_found()

        vk_group_id = institution.vk_link.split("/")[-1]

        last_review_dt = (
            Review.objects.filter(
                institution=institution,
                source=self.source_name,
            )
            .aggregate(last_date=Max("reviewed_at"))
            ["last_date"]
        )

        try:
            parser = VKReviewsParser(
                group_id=vk_group_id,
                token=settings.VK_USER_TOKEN,
                from_date=last_review_dt,
            )

            reviews_data = asyncio.run(parser.parse())

            created, skipped = save_reviews(
                institution,
                reviews_data,
                source=self.source_name,
                text_key="text",
                date_key="date",
            )

            self.run_postprocessing(created)

            return self.response_ok(
                created,
                skipped,
                total_processed=len(reviews_data),
            )

        except Exception as e:
            return Response(
                {"error": f"Error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class OtzovikReviews(BaseReviewsImportView):
    source_name = "Отзовик"

    def post(self, request):
        institution = self.get_institution(request.data.get("institution_id"))
        if not institution:
            return self.response_not_found()

        otzovik_url = institution.otzovik_link
        last_review_dt = (
            Review.objects.filter(
                institution=institution,
                source=self.source_name,
            )
            .aggregate(last_date=Max("reviewed_at"))
            ["last_date"]
        )

        try:
            parser = OtzovikReviewsParser(
                reviews_url=otzovik_url,
                from_date=last_review_dt
            )
            reviews_data = parser.parse()

            created, skipped = save_reviews(
                institution,
                reviews_data,
                source=self.source_name,
                text_key="text",
                date_key="date",
            )

            self.run_postprocessing(created)

            return self.response_ok(
                created,
                skipped,
                total_processed=len(reviews_data),
            )

        except Exception as e:
            return Response(
                {"error": f"Error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
