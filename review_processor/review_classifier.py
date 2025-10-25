import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


class OptimizedSentimentAnalyzer:
    def __init__(self, model_path, device='auto'):
        if device == 'auto':
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)

        if self.device == 'cuda':
            self.model.half()
        self.model.to(self.device)
        self.model.eval()

    def predict(self, text):
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)

        predicted_class = torch.argmax(predictions, dim=1).cpu().item()
        confidence = torch.max(predictions).cpu().item()
        probs = predictions.cpu().numpy()[0]

        return {
            'sentiment': 'positive' if predicted_class == 1 else 'negative',
            'confidence': confidence,
            'probabilities': {
                'negative': probs[0],
                'positive': probs[1]
            }
        }


review_classifier = OptimizedSentimentAnalyzer('models/classification_model')
