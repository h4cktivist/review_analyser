from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Institution, Event, Review, SuggestedActionWord
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
    def get_permissions(self):
        if self.request.method in ['GET', 'POST']:
            return [IsAuthenticated()]
        return [IsAdminUser()]

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

        institution.delete()
        return Response(
            {"message": "Institution deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )


class EventList(APIView):
    permission_classes = [AllowAny]

    def _has_worker_token(self, request):
        worker_token = getattr(settings, "EVENTS_WORKER_TOKEN", "")
        if not worker_token:
            return False

        authorization = request.headers.get("Authorization", "").strip()
        token_from_auth = ""
        if authorization:
            parts = authorization.split(" ", 1)
            if len(parts) == 2 and parts[0].lower() in {"token", "bearer"}:
                token_from_auth = parts[1].strip()

        token_from_header = request.headers.get("X-Worker-Token", "").strip()
        provided_token = token_from_auth or token_from_header
        return provided_token and provided_token == worker_token

    def _is_allowed(self, request):
        return bool(request.user and request.user.is_authenticated) or self._has_worker_token(request)

    def get(self, request):
        if not self._is_allowed(request):
            return Response({"error": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)
        events = Event.objects.all().order_by('-date')
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not self._is_allowed(request):
            return Response({"error": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventLatestDate(APIView):
    permission_classes = [AllowAny]

    def _has_worker_token(self, request):
        worker_token = getattr(settings, "EVENTS_WORKER_TOKEN", "")
        if not worker_token:
            return False

        authorization = request.headers.get("Authorization", "").strip()
        token_from_auth = ""
        if authorization:
            parts = authorization.split(" ", 1)
            if len(parts) == 2 and parts[0].lower() in {"token", "bearer"}:
                token_from_auth = parts[1].strip()

        token_from_header = request.headers.get("X-Worker-Token", "").strip()
        provided_token = token_from_auth or token_from_header
        return provided_token and provided_token == worker_token

    def _is_allowed(self, request):
        return bool(request.user and request.user.is_authenticated) or self._has_worker_token(request)

    def get(self, request):
        if not self._is_allowed(request):
            return Response({"error": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)

        latest_event = Event.objects.order_by("-date").first()
        if latest_event:
            return Response({"last_event_date": timezone.localtime(latest_event.date).isoformat()})
        return Response({"last_event_date": None})


class EventDetail(APIView):
    def get_permissions(self):
        if self.request.method in ['GET', 'POST']:
            return [IsAuthenticated()]
        return [IsAdminUser()]

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

        event.delete()
        return Response(
            {"message": "Event deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )


class ReviewList(APIView):
    def get(self, request):
        reviews = Review.objects.all().order_by("-reviewed_at")
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

class ReviewSearch(APIView):
    def get(self, request, *args, **kwargs):
        search_query = request.GET.get("q", "").strip()
        if not search_query:
            return Response({
                "results": [],
                "count": 0,
                "query": search_query,
            })

        query_filter = Q(text__icontains=search_query)
        if search_query.isdigit():
            query_filter |= Q(id=int(search_query))

        reviews = Review.objects.filter(query_filter).order_by("-reviewed_at")
        serializer = ReviewSerializer(reviews, many=True)
        return Response({
            "results": serializer.data,
            "count": len(serializer.data),
            "query": search_query,
        })

class ActionConfirmationView(APIView):
    def post(self, request, pk):
        try:
            review = Review.objects.get(pk=pk)
        except Review.DoesNotExist:
            return Response({"error": "Review not found"}, status=status.HTTP_404_NOT_FOUND)

        action_word = request.data.get("action_word")
        accepted = request.data.get("accepted")

        if not action_word or accepted is None:
            return Response({"error": "action_word and accepted are required"}, status=status.HTTP_400_BAD_REQUEST)

        if action_word not in review.potential_actions:
            return Response({"error": "Action word not found in potential actions"}, status=status.HTTP_400_BAD_REQUEST)

        review.potential_actions.remove(action_word)

        if accepted:
            if action_word not in review.required_actions:
                review.required_actions.append(action_word)
            SuggestedActionWord.objects.get_or_create(word=action_word)

        review.save()

        return Response({
            "message": "Action processed successfully",
            "required_actions": review.required_actions,
            "potential_actions": review.potential_actions
        }, status=status.HTTP_200_OK)
