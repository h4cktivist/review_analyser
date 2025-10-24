import string
from typing import List

import numpy as np
import pymorphy3
from nltk.corpus import stopwords
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from reviews.models import Event


class EventComparator:
    def __init__(self):
        self.morph = pymorphy3.MorphAnalyzer()
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.stop_words = set(stopwords.words('russian') + stopwords.words('english') + ['спектакль', 'концерт'])

    def preprocess_text(self, text: str) -> List[str]:
        text = text.lower().translate(str.maketrans('', '', string.punctuation))

        words = text.split()
        lemmas = []

        for word in words:
            parsed = self.morph.parse(word)[0]
            lemmas.append(parsed.normal_form)

        return lemmas

    def build_event_index(self, events_list: List[Event]) -> dict:
        event_index = {}
        for i, event in enumerate(events_list):
            lemmas = self.preprocess_text(event.name)

            key_lemmas = [lemma for lemma in lemmas if lemma not in self.stop_words]

            event_index[i] = {
                'event_id': event.pk,
                'key_lemmas': set(key_lemmas),
                'processed_name': ' '.join(lemmas)
            }

        return event_index

    def fast_filter(self, review_lemmas, event_index) -> list:
        candidates = []

        for event_id, event_data in event_index.items():
            key_lemmas = event_data['key_lemmas']

            if key_lemmas.intersection(review_lemmas):
                match_count = len(key_lemmas.intersection(review_lemmas))
                candidates.append((event_id, match_count))

        candidates.sort(key=lambda x: x[1], reverse=True)
        return [candidate[0] for candidate in candidates]

    def semantic_match(self, review_text, candidate_events, event_index, threshold=0.5):
        if not candidate_events:
            return None

        if len(candidate_events) == 1:
            return candidate_events[0]

        review_text_clean = ' '.join(self.preprocess_text(review_text))
        event_texts = [event_index[event_id]['processed_name'] for event_id in candidate_events]

        all_texts = [review_text_clean] + event_texts
        embeddings = self.model.encode(all_texts)

        review_embedding = embeddings[0:1]
        event_embeddings = embeddings[1:]

        similarities = cosine_similarity(review_embedding, event_embeddings)[0]

        best_match_idx = np.argmax(similarities)
        best_similarity = similarities[best_match_idx]

        if best_similarity > threshold:
            return candidate_events[best_match_idx]
        return None

    def match_review_to_event(self, review_text, event_index):
        review_lemmas = self.preprocess_text(review_text)
        candidate_ids = self.fast_filter(review_lemmas, event_index)
        matched_event_id = self.semantic_match(review_text, candidate_ids, event_index)

        if matched_event_id is not None:
            return event_index[matched_event_id]['event_id']
        return None

event_comparator = EventComparator()
