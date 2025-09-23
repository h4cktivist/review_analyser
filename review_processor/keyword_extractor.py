import re
from collections import Counter
from typing import List, Dict

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
import pymorphy3


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
    def __init__(self):
        self.stop_words = set(stopwords.words('russian') + stopwords.words('english'))
        self.morph = pymorphy3.MorphAnalyzer()

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

    def extract_tfidf_keywords(self, texts: List[str], max_keywords: int = 10) -> List[Dict]:
        if not texts:
            return []

        processed_texts = [' '.join(self.preprocess_text(text)) for text in texts]

        vectorizer = TfidfVectorizer(max_features=100, ngram_range=(1, 2))
        try:
            tfidf_matrix = vectorizer.fit_transform(processed_texts)
            feature_names = vectorizer.get_feature_names_out()

            avg_tfidf = tfidf_matrix.mean(axis=0).A1
            keywords_with_scores = list(zip(feature_names, avg_tfidf))

            keywords_with_scores.sort(key=lambda x: x[1], reverse=True)

            return [{'word': word, 'score': float(score)}
                    for word, score in keywords_with_scores[:max_keywords]]

        except ValueError:
            return self.extract_frequency_keywords(texts, max_keywords)

    def extract_frequency_keywords(self, texts: List[str], max_keywords: int = 10) -> List[Dict]:
        all_tokens = []
        for text in texts:
            tokens = self.preprocess_text(text)
            all_tokens.extend(tokens)

        word_freq = Counter(all_tokens)

        top_keywords = word_freq.most_common(max_keywords)

        return [{'word': word, 'frequency': freq}
                for word, freq in top_keywords]

    def extract_single_review_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        if not text:
            return []

        tokens = self.preprocess_text(text)
        word_freq = Counter(tokens)

        top_keywords = word_freq.most_common(max_keywords)
        return [word for word, freq in top_keywords]


keyword_extractor = KeywordExtractor()
