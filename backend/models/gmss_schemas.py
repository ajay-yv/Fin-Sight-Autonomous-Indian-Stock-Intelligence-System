from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class MacroShock(BaseModel):
    shock_id: str
    event_type: str = Field(..., description="GEOPOLITICAL, CLIMATE, FINANCIAL, or HEALTH")
    description: str
    initial_magnitude: float = Field(..., ge=0, le=1)
    target_sectors: List[str]
    duration_months: int
    started_at: datetime

class AgentState(BaseModel):
    agent_id: str
    sector: str
    sentiment: float = Field(..., ge=0, le=1)
    liquidity: float
    resilience: float = Field(..., ge=0, le=1)

class PropagationDelta(BaseModel):
    step: int
    target_sector: str
    inflation_delta: float
    supply_chain_stress: float = Field(..., ge=0, le=1)
    gdp_impact: float
    market_volatility: float

class SimulationReport(BaseModel):
    simulation_id: str
    shock: MacroShock
    propagation_steps: List[PropagationDelta]
    affected_sectors: List[str]
    max_supply_chain_stress: float
    recovery_estimated_months: int
    narrative_summary: str
