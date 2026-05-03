import asyncio
from typing import Any

from django.conf import settings
from django.db import transaction
from django.db.models import Max

from importer.services.gis_importer import fetch_reviews_with_pagination
from importer.services.ok_importer import fetch_ok_comments
from importer.services.otzovik_importer import OtzovikReviewsParser
from importer.services.telegram_importer import parse_telegram_comments
from importer.services.vk_importer import VKReviewsParser
from importer.services.yandex_importer import yandex_reviews_importer
from reviews.models import Institution, Review

SOURCE_GIS = "2GIS"
SOURCE_YANDEX = "Яндекс Карты"
SOURCE_TELEGRAM = "Telegram"
SOURCE_VK = "VK"
SOURCE_OTZOVIK = "Отзовик"
SOURCE_OK = "Одноклассники"


def _last_url_path_part(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def save_reviews(
    institution: Institution,
    reviews_data: list[dict[str, Any]],
    source: str,
    text_key: str,
    date_key: str,
) -> tuple[list[Review], int]:
    existing_texts = set(
        Review.objects.filter(
            institution=institution
        ).values_list("text", flat=True)
    )

    new_reviews: list[Review] = []
    skipped_count = 0

    for data in reviews_data:
        text = data.get(text_key)
        reviewed_at = data.get(date_key)
        if not text or reviewed_at is None:
            skipped_count += 1
            continue

        if text in existing_texts:
            skipped_count += 1
            continue

        new_reviews.append(
            Review(
                institution=institution,
                text=text,
                source=source,
                reviewed_at=reviewed_at,
            )
        )

    with transaction.atomic():
        created_reviews = Review.objects.bulk_create(new_reviews)

    return created_reviews, skipped_count


def _get_last_review_dt(institution: Institution, source: str):
    return (
        Review.objects.filter(
            institution=institution,
            source=source,
        )
        .aggregate(last_date=Max("reviewed_at"))
        ["last_date"]
    )


def _serialize_import_result(
    source: str,
    created: list[Review],
    skipped_count: int,
    total_processed: int,
) -> dict[str, Any]:
    return {
        "source": source,
        "imported_count": len(created),
        "skipped_count": skipped_count,
        "total_processed": total_processed,
        "created_review_ids": [review.id for review in created],
    }


def import_gis_reviews(institution_id: int) -> dict[str, Any]:
    institution = Institution.objects.get(pk=institution_id)

    gis_id = int(_last_url_path_part(institution.gis_map_link))
    url = (
        "https://public-api.reviews.2gis.com/3.0/branches/"
        f"{gis_id}/reviews?limit=50&key={settings.GIS_KEY}"
        "&locale=ru_RU&sort_by=date_created"
    )

    reviews_data = fetch_reviews_with_pagination(
        initial_url=url,
        auth_header=f"Bearer {settings.GIS_AUTH_TOKEN}",
    )

    created, skipped = save_reviews(
        institution,
        reviews_data,
        source=SOURCE_GIS,
        text_key="text",
        date_key="date_created",
    )

    return _serialize_import_result(
        source=SOURCE_GIS,
        created=created,
        skipped_count=skipped,
        total_processed=len(reviews_data),
    )


def import_yandex_reviews(institution_id: int) -> dict[str, Any]:
    institution = Institution.objects.get(pk=institution_id)
    yandex_id = int(_last_url_path_part(institution.yandex_map_link))

    data = yandex_reviews_importer.parse_reviews(yandex_id=yandex_id)
    reviews = data.get("company_reviews", [])

    created, skipped = save_reviews(
        institution,
        reviews,
        source=SOURCE_YANDEX,
        text_key="text",
        date_key="date",
    )

    return _serialize_import_result(
        source=SOURCE_YANDEX,
        created=created,
        skipped_count=skipped,
        total_processed=len(reviews),
    )


def import_telegram_reviews(institution_id: int) -> dict[str, Any]:
    institution = Institution.objects.get(pk=institution_id)
    tg_channel = _last_url_path_part(institution.telegram_link)
    last_review_dt = _get_last_review_dt(institution, SOURCE_TELEGRAM)

    reviews = parse_telegram_comments(
        channel_username=tg_channel,
        since_dt=last_review_dt,
    )

    created, skipped = save_reviews(
        institution,
        reviews,
        source=SOURCE_TELEGRAM,
        text_key="text",
        date_key="date",
    )

    return _serialize_import_result(
        source=SOURCE_TELEGRAM,
        created=created,
        skipped_count=skipped,
        total_processed=len(reviews),
    )


def import_vk_reviews(institution_id: int, vk_access_token: str) -> dict[str, Any]:
    institution = Institution.objects.get(pk=institution_id)
    vk_group_id = _last_url_path_part(institution.vk_link)
    last_review_dt = _get_last_review_dt(institution, SOURCE_VK)

    parser = VKReviewsParser(
        group_id=vk_group_id,
        token=vk_access_token,
        from_date=last_review_dt,
    )
    reviews_data = asyncio.run(parser.parse())

    created, skipped = save_reviews(
        institution,
        reviews_data,
        source=SOURCE_VK,
        text_key="text",
        date_key="date",
    )

    return _serialize_import_result(
        source=SOURCE_VK,
        created=created,
        skipped_count=skipped,
        total_processed=len(reviews_data),
    )


def import_otzovik_reviews(institution_id: int) -> dict[str, Any]:
    institution = Institution.objects.get(pk=institution_id)
    last_review_dt = _get_last_review_dt(institution, SOURCE_OTZOVIK)

    parser = OtzovikReviewsParser(
        reviews_url=institution.otzovik_link,
        from_date=last_review_dt,
    )
    reviews_data = parser.parse()

    created, skipped = save_reviews(
        institution,
        reviews_data,
        source=SOURCE_OTZOVIK,
        text_key="text",
        date_key="date",
    )

    return _serialize_import_result(
        source=SOURCE_OTZOVIK,
        created=created,
        skipped_count=skipped,
        total_processed=len(reviews_data),
    )


def import_ok_reviews(institution_id: int) -> dict[str, Any]:
    institution = Institution.objects.get(pk=institution_id)
    ok_group_id = _last_url_path_part(institution.ok_link)

    reviews_data = fetch_ok_comments(group_id=ok_group_id)

    created, skipped = save_reviews(
        institution,
        reviews_data,
        source=SOURCE_OK,
        text_key="text",
        date_key="date",
    )

    return _serialize_import_result(
        source=SOURCE_OK,
        created=created,
        skipped_count=skipped,
        total_processed=len(reviews_data),
    )
