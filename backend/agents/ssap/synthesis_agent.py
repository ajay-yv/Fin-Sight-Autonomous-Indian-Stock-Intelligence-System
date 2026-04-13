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
                f"Operational analysis detects high activity density ({geo.density_score*100:.1f}%) "
                f"based on recent corporate footprints. However, news-based sentiment remains muted ({sentiment.sentiment_score:.2f}). "
                "This divergence suggests latent strength that the broader market has not yet prioritized."
            )
        elif geo.density_score < 0.4 and sentiment.sentiment_score > 0.6:
            prediction = "BEARISH_SURPRISE"
            discrepancy = True
            reasoning = (
                f"Market sentiment is overly optimistic ({sentiment.sentiment_score:.2f}), "
                f"but operational tracking shows a low intensity signal ({geo.density_score*100:.1f}%). "
                "The fundamental operational data does not support the digital sentiment, suggesting a downside surprise."
            )
        else:
            reasoning = "Operational signals and news sentiment are fundamentally aligned. No significant alpha discrepancy detected."
 
        return SSAPVerdict(
            symbol=symbol,
            run_id=f"SSAP-{datetime.now().strftime('%Y%j%H%M')}",
            timestamp=datetime.now(),
            geospatial_summary=f"Operational signal type: {geo.activity_type} (Intensity: {geo.density_score*100:.1f}%).",
            sentiment_summary=f"Analysis of latest {sentiment.mention_volume/100:.0f} news cycles yields {sentiment.sentiment_score:.2f} score.",
            alpha_discrepancy=discrepancy,
            discrepancy_score=discrepancy_score,
            prediction=prediction,
            reasoning=reasoning,
            confidence_score=(geo.confidence + sentiment.trending_score) / 2
        )
