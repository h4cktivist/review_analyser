from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.db import transaction
from django.conf import settings

from reviews.models import Institution, Review
from reviews.serializers import ReviewSerializer
from .gis_importer import fetch_reviews_with_pagination
from .tasks import extract_aspects_for_review, compare_review_with_event, classify_review_sentiment


class GISReviews(APIView):
    def get_object(self, pk):
        try:
            return Institution.objects.get(pk=pk)
        except Institution.DoesNotExist:
            return None

    def post(self, request):
        institution = self.get_object(request.data.get("institution_id"))
        if institution is None:
            return Response(
                {"error": "Institution is not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        institution_gis_id = int(institution.gis_map_link.split("/")[-1])

        url = f"https://public-api.reviews.2gis.com/3.0/branches/{institution_gis_id}/reviews?limit=50&key={settings.GIS_KEY}&locale=ru_RU&sort_by=date_created"
        auth_header = f"Bearer {settings.GIS_AUTH_TOKEN}"

        try:
            reviews_data = fetch_reviews_with_pagination(
                initial_url=url,
                auth_header=auth_header
            )

            saved_count, skipped_count = 0, 0
            with transaction.atomic():
                for review_data in reviews_data:
                    if not Review.objects.filter(
                            institution_id=institution.pk,
                            text=review_data["text"],
                    ).exists():
                        Review.objects.create(
                            institution_id=institution.pk,
                            text=review_data["text"],
                            reviewed_at=review_data["date_created"],
                        )
                        saved_count += 1
                else:
                    skipped_count += 1

            imported_reviews = Review.objects.order_by("-created_at")[:saved_count]
            if imported_reviews:
                for review in imported_reviews:
                    compare_review_with_event.delay(review.id)
                    classify_review_sentiment.delay(review.id)
                    extract_aspects_for_review.delay(review.id)

            serializer = ReviewSerializer(imported_reviews, many=True)

            return Response({
                "message": f"Successfully imported {saved_count} reviews, skipped {skipped_count} duplicates",
                "imported_reviews": serializer.data,
                "total_processed": len(reviews_data)
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                "error": f"Error occured: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
