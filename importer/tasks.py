from celery import shared_task

from reviews.models import Review, Event
from review_processor.event_comparator import event_comparator
from review_processor.keyword_extractor import keyword_extractor
from review_processor.review_classifier import review_classifier


@shared_task
def extract_keywords_for_review(review_id: int):
    try:
        review = Review.objects.get(id=review_id)

        if not review.text:
            review.keywords = []
            review.keywords_processed = True
            review.save()
            return

        keywords = keyword_extractor.extract_single_review_keywords(review.text)

        review.keywords = keywords
        review.keywords_processed = True
        review.save()

        print(f"Review {review_id} was processed, number of keywords: {len(keywords)}")

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
def classify_review_sentiment(review_id: int):
    try:
        review = Review.objects.get(id=review_id)
        if not review:
            return

        cls_result = review_classifier.predict(text=review.text)
        if abs(cls_result['probabilities']['negative'] - cls_result['probabilities']['positive']) < 0.15:
            review.sentiment = 'neutral'
        else:
            review.sentiment = cls_result['sentiment']
            review.confidence = cls_result['confidence']
        review.save()

    except Review.DoesNotExist:
        print(f"Review {review_id} is not found")
    except Exception as e:
        print(f"Error with review {review_id}: {str(e)}")
