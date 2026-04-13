import os
import torch
from transformers import BertTokenizer, BertForSequenceClassification, pipeline

class SentimentEngine:
    """
    Institutional-grade sentiment analysis engine using FinBERT.
    Provides localized, domain-specific sentiment scoring for Indian markets.
    """
    def __init__(self, model_name: str = "yiyanghkust/finbert-tone"):
        self.model_name = model_name
        self.device = 0 if torch.cuda.is_available() else -1
        self._nlp = None
        self._enabled = False
        
        # Optionally pre-load if environment variable is set
        if os.getenv("LOAD_FINBERT", "false").lower() == "true":
            self.load_model()

    def load_model(self):
        """Loads the FinBERT model into memory."""
        try:
            print(f"Loading FinBERT model: {self.model_name}...")
            tokenizer = BertTokenizer.from_pretrained(self.model_name)
            model = BertForSequenceClassification.from_pretrained(self.model_name)
            self._nlp = pipeline(
                "sentiment-analysis", 
                model=model, 
                tokenizer=tokenizer, 
                device=self.device
            )
            self._enabled = True
            print("FinBERT model loaded successfully.")
        except Exception as e:
            print(f"Failed to load FinBERT model: {e}")
            self._enabled = False

    def analyze_headlines(self, headlines: list[str]) -> dict:
        """
        Analyzes a list of financial headlines.
        Returns a structured sentiment profile.
        """
        if not self._enabled or not self._nlp:
            return {
                "sentiment_label": "neutral",
                "score": 0.0,
                "confidence": 0.5,
                "is_live": False,
                "engine": "Fallback-Heuristic"
            }

        try:
            results = self._nlp(headlines)
            
            # Map labels to scores: Positive: 1.0, Neutral: 0.0, Negative: -1.0
            label_map = {"Positive": 1.0, "Neutral": 0.0, "Negative": -1.0}
            
            scores = []
            confidences = []
            
            for res in results:
                label = res['label']
                score = label_map.get(label, 0.0)
                scores.append(score)
                confidences.append(res['score'])
            
            avg_score = sum(scores) / len(scores) if scores else 0.0
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.5
            
            final_label = "positive" if avg_score > 0.2 else "negative" if avg_score < -0.2 else "neutral"
            
            return {
                "sentiment_label": final_label,
                "score": avg_score,
                "confidence": avg_conf,
                "is_live": True,
                "engine": f"FinBERT ({self.model_name})"
            }
        except Exception as e:
            print(f"Error during FinBERT analysis: {e}")
            return {
                "sentiment_label": "neutral",
                "score": 0.0,
                "confidence": 0.0,
                "is_live": False,
                "engine": "Error-Fallback"
            }

# Global instance for shared use
sentiment_engine = SentimentEngine()
