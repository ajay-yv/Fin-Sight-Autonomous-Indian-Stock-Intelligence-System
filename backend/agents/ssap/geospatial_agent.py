import logging
import random
from datetime import datetime, timedelta
from typing import Dict
from backend.models.ssap_schemas import SatelliteInsight

logger = logging.getLogger(__name__)

from backend.services.intelligence_service import IntelligenceService

class GeospatialAgent:
    """
    Analyzes corporate footprints and operational activity.
    In this upgrade, it synthesizes 'Operational Heat' from news and reports.
    """
    def __init__(self):
        self.name = "OperationalInsight"
        self.intel = IntelligenceService()

    async def get_latest_insight(self, symbol: str) -> SatelliteInsight:
        """
        Extracts operational signals from latest news and corporate disclosures.
        """
        logger.info(f"Analyzing operational signal for: {symbol}")
        
        # In a real-world scenario, we'd use satellite coordinates.
        # Here we simulate 'Activity Density' by cross-referencing news about 
        # facility expansions, job openings, or production surges.
        ticker_symbol = symbol if symbol.endswith((".NS", ".BO")) else f"{symbol}.NS"
        news_data = await self.intel.get_symbol_news_sentiment(ticker_symbol)
        headlines = news_data.get("headlines", [])
        
        # Search for operation-heavy keywords
        op_keywords = {"factory", "plant", "expansion", "hiring", "logistics", "production", "supply"}
        matches = sum(1 for h in headlines if any(k in h.lower() for k in op_keywords))
        
        # Calculate density based on 'Operational Buzz'
        density = 0.4 + (matches * 0.15)
        density = min(1.0, density)
        
        activity_type = "OPERATIONAL_EXPANSION" if matches > 0 else "ROUTINE_OPERATIONS"

        # Dynamically change image based on activity intensity
        if density > 0.7:
             image_url = "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?auto=format&fit=crop&q=80&w=1000" # Advanced Factory
        else:
             image_url = "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&q=80&w=1000" # Standard Logistics

        return SatelliteInsight(
            area_id=f"{symbol}_GLOBAL_HUB",
            timestamp=datetime.now(),
            activity_type=activity_type,
            density_score=density,
            object_counts={"operational_signal_strength": matches},
            image_url=image_url,
            confidence=0.85
        )

class SyncAnalysisAgent:
    """
    Fuses geospatial and sentiment signals.
    """
    def __init__(self):
         self.name = "MultimodalFusion"
