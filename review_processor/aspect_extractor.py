from pyabsa import ATEPCCheckpointManager


class AspectExtractor:
    def __init__(self):
        self.extractor = ATEPCCheckpointManager.get_aspect_extractor(
            checkpoint="models/aspect_extraction_model",
            auto_device=True
        )

    def extract_aspects(self, text: str):
        if not text or not text.strip():
            return [], []

        aspects = self.extractor.extract_aspect([f"{text}"])

        if not aspects or not aspects[0]:
            return [], []

        positive_aspects, negative_aspects = list(), list()
        aspect_list = aspects[0].get("aspect", [])
        sentiment_list = aspects[0].get("sentiment", [])

        for aspect, sentiment in zip(aspect_list, sentiment_list):
            if sentiment == "Negative":
                negative_aspects.append(aspect)
            else:
                positive_aspects.append(aspect)

        return positive_aspects, negative_aspects


aspect_extractor = AspectExtractor()
