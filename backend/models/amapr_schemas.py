from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class AssetClass(str, Enum):
    EQUITY = "EQUITY"
    REAL_ESTATE = "REAL_ESTATE"
    PRIVATE_CREDIT = "PRIVATE_CREDIT"
    COMMODITY = "COMMODITY"
    CASH = "CASH"

class RWAData(BaseModel):
    """Schema for Real-World Assets."""
    asset_id: str
    name: str
    asset_class: AssetClass
    token_address: Optional[str] = None
    valuation_usd: float
    liquidity_score: float = Field(..., ge=0, le=1)
    apy: float
    volatility: float
    last_updated: datetime

class PortfolioAsset(BaseModel):
    symbol: str
    asset_class: AssetClass
    units: float
    current_price: float
    valuation: float
    weight: float

class PortfolioState(BaseModel):
    portfolio_id: str
    assets: List[PortfolioAsset]
    total_valuation: float
    target_weights: Dict[AssetClass, float]
    drift_score: float
    last_rebalanced: Optional[datetime] = None

class AgentProposal(BaseModel):
    agent_name: str
    action: str  # e.g., "BUY", "SELL", "HOLD"
    symbol: str
    units: float
    reasoning: str
    tax_impact: Optional[float] = None
    risk_impact: Optional[float] = None
    esg_impact: Optional[float] = None

class NegotiationStep(BaseModel):
    step_index: int
    proposals: List[AgentProposal]
    consensus_reached: bool
    conflict_notes: Optional[str] = None

class AMAPRRunResult(BaseModel):
    run_id: str
    initial_state: PortfolioState
    final_state: PortfolioState
    negotiation_history: List[NegotiationStep]
    total_tax_optimized: float
    risk_reduction: float
    timestamp: datetime
