from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class SatelliteInsight(BaseModel):
    area_id: str
    timestamp: datetime
    activity_type: str = Field(..., description="e.g., RETAIL_TRAFFIC, LOGISTICS_CONGESTION")
    density_score: float = Field(..., ge=0, le=1, description="Relative density score")
    object_counts: Dict[str, int] = Field(default_factory=dict, description="e.g., {'cars': 150, 'trucks': 12}")
    image_url: Optional[str] = None
    confidence: float

class SentimentInsight(BaseModel):
    protocol: str = Field(..., description="Farcaster or Lens")
    symbol: str
    timestamp: datetime
    mention_volume: int
    sentiment_score: float = Field(..., ge=-1, le=1)
    top_keywords: List[str]
    trending_score: float
    raw_sample_posts: List[str]

class SSAPVerdict(BaseModel):
    symbol: str
    run_id: str
    timestamp: datetime
    geospatial_summary: str
    sentiment_summary: str
    alpha_discrepancy: bool
    discrepancy_score: float = Field(..., description="Intensity of the discrepancy")
    prediction: str = Field(..., description="BULLISH_SURPRISE, BEARISH_SURPRISE, NEUTRAL")
    reasoning: str
    confidence_score: float
