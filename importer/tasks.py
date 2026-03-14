import httpx
from celery import shared_task
from decouple import config

from reviews.models import Review, Event
from review_processor.event_comparator import event_comparator
from review_processor.profanity_wrapper import get_wrapped_prof_words
from review_processor.action_extractor import extract_actions

ANALYSIS_SERVICE_URL = config("ANALYSIS_SERVICE_URL", default="http://localhost:8001")
_REQUEST_TIMEOUT = 120


def _call_analyze(text: str) -> dict:
    response = httpx.post(
        f"{ANALYSIS_SERVICE_URL}/analyze",
        json={"text": text},
        timeout=_REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


@shared_task
def analyze_review(review_id: int):
    try:
        review = Review.objects.get(id=review_id)

        if not review.text:
            review.positive_aspects = []
            review.negative_aspects = []
            review.save()
            return

        result = _call_analyze(review.text)

        required_actions, potential_actions = extract_actions(review.text)

        review.sentiment = result["sentiment"]
        review.confidence = result["confidence"]
        review.positive_aspects = result["positive_aspects"]
        review.negative_aspects = result["negative_aspects"]
        review.required_actions = required_actions
        review.potential_actions = potential_actions
        review.save()

        print(f"Review {review_id} analyzed: sentiment={result['sentiment']}")

    except Review.DoesNotExist:
        print(f"Review {review_id} is not found")
    except Exception as e:
        print(f"Error with review {review_id}: {str(e)}")


@shared_task
def compare_review_with_event(review_id: int):
    try:
        review = Review.objects.get(id=review_id)
        if not review:
            return

        events = list(Event.objects.all())
        event_index = event_comparator.build_event_index(events_list=events)

        event_id = event_comparator.match_review_to_event(
            review_text=review.text, event_index=event_index
        )
        review.event = Event.objects.get(id=event_id)
        review.save()

        print(f"Review {review_id} was processed, compared event ID: {event_id}")

    except Review.DoesNotExist:
        print(f"Review {review_id} is not found")
    except Exception as e:
        print(f"Error with review {review_id}: {str(e)}")


@shared_task
def wrap_profanity(review_id: int):
    try:
        review = Review.objects.get(id=review_id)
        if not review:
            return

        review.text = get_wrapped_prof_words(review.text)
        review.save()

    except Review.DoesNotExist:
        print(f"Review {review_id} is not found")
    except Exception as e:
        print(f"Error with review {review_id}: {str(e)}")
