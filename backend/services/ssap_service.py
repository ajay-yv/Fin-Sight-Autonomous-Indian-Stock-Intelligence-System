import logging
from datetime import datetime
from typing import Dict
from backend.models.ssap_schemas import SSAPVerdict
from backend.agents.ssap.geospatial_agent import GeospatialAgent
from backend.agents.ssap.sentiment_agent import SentimentAgent
from backend.agents.ssap.synthesis_agent import MultimodalSynthesisAgent

logger = logging.getLogger(__name__)

class SSAPService:
    """
    Orchestrates the Satellite-to-Sentiment Alpha Predictor workflow.
    Fuses geospatial and social intelligence to identify market discrepancies.
    """
    def __init__(self):
        self.geo_agent = GeospatialAgent()
        self.sentiment_agent = SentimentAgent()
        self.synthesis_agent = MultimodalSynthesisAgent()
        # In-memory store for prototype
        self.history: Dict[str, SSAPVerdict] = {}

    async def run_analysis(self, symbol: str) -> SSAPVerdict:
        """
        Runs the full multimodal analysis pipeline for a target symbol.
        """
        logger.info(f"Starting SSAP Analysis for {symbol}")
        
        # Phase 1: Collect Signals
        geo_insight = await self.geo_agent.get_latest_insight(symbol)
        sentiment_insight = await self.sentiment_agent.analyze_sentiment(symbol)
        
        # Phase 2: Multimodal Fusion
        verdict = await self.synthesis_agent.fuse_signals(symbol, geo_insight, sentiment_insight)
        
        # Phase 3: Persist & Return
        self.history[symbol] = verdict
        return verdict

    def get_latest_verdict(self, symbol: str) -> SSAPVerdict:
        return self.history.get(symbol)
