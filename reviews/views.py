from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Institution, Event, Review
from .serializers import InstitutionSerializer, EventSerializer, ReviewSerializer


class InstitutionList(APIView):
    def get(self, request):
        institutions = Institution.objects.all()
        serializer = InstitutionSerializer(institutions, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = InstitutionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InstitutionDetail(APIView):
    def get_object(self, pk):
        try:
            return Institution.objects.get(pk=pk)
        except Institution.DoesNotExist:
            return None

    def get(self, request, pk):
        institution = self.get_object(pk)
        if institution is None:
            return Response(
                {"error": "Institution is not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = InstitutionSerializer(institution)
        return Response(serializer.data)

    def put(self, request, pk):
        institution = self.get_object(pk)
        if institution is None:
            return Response(
                {"error": "Institution is not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = InstitutionSerializer(institution, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        institution = self.get_object(pk)
        if institution is None:
            return Response(
                {"error": "Institution is not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if institution.reviews.exists():
            return Response(
                {"error": "Can't remove institution with related reviews"},
                status=status.HTTP_400_BAD_REQUEST
            )

        institution.delete()
        return Response(
            {"message": "Institution deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )


class EventList(APIView):
    def get(self, request):
        events = Event.objects.all()
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventDetail(APIView):
    def get_object(self, pk):
        try:
            return Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            return None

    def get(self, request, pk):
        event = self.get_object(pk)
        if event is None:
            return Response(
                {"error": "Event is not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = EventSerializer(event)
        return Response(serializer.data)

    def put(self, request, pk):
        event = self.get_object(pk)
        if event is None:
            return Response(
                {"error": "Event is not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EventSerializer(event, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        event = self.get_object(pk)
        if event is None:
            return Response(
                {"error": "Event is not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if event.reviews.exists():
            return Response(
                {"error": "Can't remove event with related reviews"},
                status=status.HTTP_400_BAD_REQUEST
            )

        event.delete()
        return Response(
            {"message": "Event deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )


class ReviewList(APIView):
    def get(self, request):
        reviews = Review.objects.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            review = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewDetail(APIView):
    def get_object(self, pk):
        try:
            return Review.objects.get(pk=pk)
        except Review.DoesNotExist:
            return None

    def get(self, request, pk):
        review = self.get_object(pk)
        if review is None:
            return Response(
                {"error": "Review is not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = ReviewSerializer(review)
        return Response(serializer.data)

    def put(self, request, pk):
        review = self.get_object(pk)
        if review is None:
            return Response(
                {"error": "Review is not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ReviewSerializer(review, data=request.data)
        if serializer.is_valid():
            updated_review = serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        review = self.get_object(pk)
        if review is None:
            return Response(
                {"error": "Review is not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        review.delete()
        return Response(
            {"message": "Review deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
