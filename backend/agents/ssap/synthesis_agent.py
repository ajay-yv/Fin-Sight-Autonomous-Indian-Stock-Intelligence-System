import logging
from datetime import datetime
from backend.models.ssap_schemas import SSAPVerdict, SatelliteInsight, SentimentInsight

logger = logging.getLogger(__name__)

class MultimodalSynthesisAgent:
    """
    Fuses geospatial and social sentiment insights to predict earnings surprises.
    The goal is to detect 'Alpha Discrepancies' where physical and digital data diverge.
    """
    def __init__(self):
        self.name = "MultimodalSynthesis"

    async def fuse_signals(self, symbol: str, geo: SatelliteInsight, sentiment: SentimentInsight) -> SSAPVerdict:
        """
        Synthesizes multimodal data to identify alpha opportunities.
        """
        logger.info(f"Fusing signals for {symbol}")
        
        # Alpha Detection Logic:
        # High Physical Activity (>0.75 density) + Low Social Sentiment (<0.2) = BULLISH SURPRISE
        # Low Physical Activity (<0.4 density) + High Social Sentiment (>0.6) = BEARISH SURPRISE
        
        discrepancy = False
        discrepancy_score = abs(geo.density_score - sentiment.sentiment_score)
        prediction = "NEUTRAL"
        
        if geo.density_score > 0.75 and sentiment.sentiment_score < 0.3:
            prediction = "BULLISH_SURPRISE"
            discrepancy = True
            reasoning = (
                f"Satellite imagery detects high retail density ({geo.object_counts.get('cars', 0)} vehicles), "
                f"indicating strong physical demand. However, Farcaster sentiment is muted ({sentiment.sentiment_score:.2f}). "
                "This divergence suggests an imminent earnings beat that the market has not yet priced in."
            )
        elif geo.density_score < 0.4 and sentiment.sentiment_score > 0.6:
            prediction = "BEARISH_SURPRISE"
            discrepancy = True
            reasoning = (
                f"Social sentiment is overly optimistic ({sentiment.sentiment_score:.2f}), "
                f"but satellite tracking shows declining foot traffic ({geo.density_score*100:.1f}%) and logistic slowdowns. "
                "The physical data does not support the digital hype, suggesting a downside surprise."
            )
        else:
            reasoning = "Physical activity and social sentiment are aligned. No significant alpha discrepancy detected."

        return SSAPVerdict(
            symbol=symbol,
            run_id=f"SSAP-{datetime.now().strftime('%Y%j%H%M')}",
            timestamp=datetime.now(),
            geospatial_summary=f"Detected {geo.object_counts.get('cars', 0)} cars in {geo.activity_type}.",
            sentiment_summary=f"Sentiment score of {sentiment.sentiment_score:.2f} across {sentiment.mention_volume} DeSo posts.",
            alpha_discrepancy=discrepancy,
            discrepancy_score=discrepancy_score,
            prediction=prediction,
            reasoning=reasoning,
            confidence_score=(geo.confidence + sentiment.trending_score) / 2
        )
