from analysis_service.utils.review_classifier import OptimizedSentimentAnalyzer
from analysis_service.utils.aspect_extractor import AspectExtractor

_SENTIMENT_THRESHOLD = 0.15


class _ModelRegistry:
    classifier: OptimizedSentimentAnalyzer | None = None
    extractor: AspectExtractor | None = None

    @classmethod
    def load(cls) -> None:
        print("Loading sentiment classifier...")
        cls.classifier = OptimizedSentimentAnalyzer("models/classification_model")
        print("Loading aspect extractor...")
        cls.extractor = AspectExtractor()
        print("Models loaded.")

    @classmethod
    def is_ready(cls) -> bool:
        return cls.classifier is not None and cls.extractor is not None


def load_models() -> None:
    _ModelRegistry.load()


def analyze(text: str) -> dict:
    if not _ModelRegistry.is_ready():
        raise RuntimeError("Models are not loaded. Call load_models() first.")

    cls_result = _ModelRegistry.classifier.predict(text)
    neg_prob = cls_result["probabilities"]["negative"]
    pos_prob = cls_result["probabilities"]["positive"]

    if abs(neg_prob - pos_prob) < _SENTIMENT_THRESHOLD:
        sentiment = "neutral"
        confidence = cls_result["confidence"]
    else:
        sentiment = cls_result["sentiment"]
        confidence = cls_result["confidence"]

    if text and text.strip():
        positive_aspects, negative_aspects = _ModelRegistry.extractor.extract_aspects(text)
    else:
        positive_aspects, negative_aspects = [], []

    return {
        "sentiment": sentiment,
        "confidence": confidence,
        "positive_aspects": positive_aspects,
        "negative_aspects": negative_aspects,
    }
