import re
from typing import List, Dict
from collections import Counter

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import pymorphy3
import yake

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('tokenizers/punkt_tab/russian/')
except LookupError:
    nltk.download('punkt_tab')


class KeywordExtractor:
    def __init__(self, language: str = "ru", n_gram_size: int = 2, deduplication_threshold: float = 0.9,
                 num_keywords: int = 10, deduplication_function: str = "seqm"):
        self.stop_words = set(stopwords.words('russian') + stopwords.words('english'))
        self.morph = pymorphy3.MorphAnalyzer()

        self.yake_extractor = yake.KeywordExtractor(
            lan=language,
            n=n_gram_size,
            dedupLim=deduplication_threshold,
            top=num_keywords,
            dedupFunc=deduplication_function
        )

        self.num_keywords = num_keywords

    def preprocess_text(self, text: str) -> List[str]:
        if not text:
            return []

        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', '', text)

        tokens = word_tokenize(text, language='russian')
        tokens = [token for token in tokens if token not in self.stop_words and len(token) > 2]

        lemmatized_tokens = []
        for token in tokens:
            try:
                parsed = self.morph.parse(token)[0]
                lemma = parsed.normal_form
                lemmatized_tokens.append(lemma)
            except Exception:
                lemmatized_tokens.append(token)

        return lemmatized_tokens

    def extract_yake_single_text(self, text: str, max_keywords: int = 5) -> List[Dict]:
        if not text:
            return []

        try:
            keywords = self.yake_extractor.extract_keywords(text)
            keywords_with_scores = [(keyword, 1 - score) for keyword, score in keywords]
            keywords_with_scores.sort(key=lambda x: x[1], reverse=True)

            return [{'word': word, 'score': float(score)}
                    for word, score in keywords_with_scores[:max_keywords]]

        except Exception as e:
            print(f"YAKE single text extraction failed: {e}")
            return self.extract_frequency_single_text(text, max_keywords)

    def extract_frequency_keywords(self, texts: List[str], max_keywords: int = 10) -> List[Dict]:
        all_tokens = []
        for text in texts:
            tokens = self.preprocess_text(text)
            all_tokens.extend(tokens)

        word_freq = Counter(all_tokens)
        top_keywords = word_freq.most_common(max_keywords)

        return [{'word': word, 'frequency': freq}
                for word, freq in top_keywords]

    def extract_frequency_single_text(self, text: str, max_keywords: int = 5) -> List[Dict]:
        if not text:
            return []

        tokens = self.preprocess_text(text)
        word_freq = Counter(tokens)
        top_keywords = word_freq.most_common(max_keywords)

        return [{'word': word, 'frequency': freq}
                for word, freq in top_keywords]

    def extract_single_review_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        keywords = self.extract_yake_single_text(text, max_keywords)
        return [keyword['word'] for keyword in keywords]

keyword_extractor = KeywordExtractor(
    language="ru",
    n_gram_size=2,
    deduplication_threshold=0.9,
    num_keywords=10
)
