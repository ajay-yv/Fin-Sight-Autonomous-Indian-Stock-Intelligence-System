"""
FinSight — Intelligence Context.
A unified data structure to hold all pre-fetched information for a symbol,
preventing redundant network calls and ensuring data consistency.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from backend.models.schemas import OHLCVData

class IntelligenceContext(BaseModel):
    """
    Shared context for a single stock symbol.
    Passed to all specialized agents (technical, fundamental, sentiment, etc.)
    """
    symbol: str
    ohlcv: OHLCVData
    ticker_info: Dict[str, Any] = Field(default_factory=dict)
    headlines: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # Allows agents to store intermediate results if needed
    cache: Dict[str, Any] = Field(default_factory=dict)

    def get_metric(self, key: str, default: Any = None) -> Any:
        """Helper to get a metric from ticker_info or metadata."""
        return self.ticker_info.get(key) or self.metadata.get(key) or default
