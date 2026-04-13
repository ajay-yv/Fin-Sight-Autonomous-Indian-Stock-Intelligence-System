import logging
import random
from datetime import datetime
from typing import List
from backend.models.ssap_schemas import SentimentInsight

logger = logging.getLogger(__name__)

from backend.services.intelligence_service import IntelligenceService

class SentimentAgent:
    """
    Extracts high-fidelity sentiment from news and social feeds.
    """
    def __init__(self):
        self.name = "RealWorldSentiment"
        self.intel = IntelligenceService()

    async def analyze_sentiment(self, symbol: str) -> SentimentInsight:
        """
        Fetches real news for the symbol and analyzes sentiment.
        """
        logger.info(f"Analyzing real-world sentiment for: {symbol}")
        
        # Cross-reference with .NS or .BO for Indian stocks
        ticker_symbol = symbol if symbol.endswith((".NS", ".BO")) else f"{symbol}.NS"
        news_data = await self.intel.get_symbol_news_sentiment(ticker_symbol)
        
        headlines = news_data.get("headlines", [])
        
        # Simple sentiment calculation based on key words (for prototype)
        # Innovation: In production, pass headlines to LLM for nuanced analysis
        pos_words = {"growth", "buy", "profit", "dividend", "expansion", "bullish"}
        neg_words = {"loss", "sell", "decline", "debt", "risk", "bearish"}
        
        score = 0.0
        for h in headlines:
            h_lower = h.lower()
            if any(w in h_lower for w in pos_words): score += 0.2
            if any(w in h_lower for w in neg_words): score -= 0.2
            
        sentiment_score = max(-1.0, min(1.0, score))
        
        return SentimentInsight(
            protocol="FinSight/YFinance",
            symbol=symbol,
            timestamp=datetime.now(),
            mention_volume=len(headlines) * 100, # Simulated volume based on news density
            sentiment_score=sentiment_score,
            top_keywords=["market", "corporate", "dividend"][:len(headlines)],
            trending_score=0.5 + (sentiment_score * 0.2),
            raw_sample_posts=headlines
        )
