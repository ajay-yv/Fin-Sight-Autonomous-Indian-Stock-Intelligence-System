from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime

from backend.models.amapr_schemas import PortfolioState, AMAPRRunResult
from backend.services.amapr_service import AMAPRService

router = APIRouter(prefix="/api/amapr", tags=["AMAPR"])
amapr_service = AMAPRService()

@router.get("/portfolio", response_model=PortfolioState)
async def get_portfolio_state():
    """Retrieve the current portfolio state with tradition assets and RWAs."""
    return await amapr_service.get_portfolio()

@router.post("/portfolio", response_model=PortfolioState)
async def update_portfolio(state: PortfolioState):
    """Update the current portfolio state."""
    amapr_service.update_portfolio(state)
    return await amapr_service.get_portfolio()

@router.post("/rebalance", response_model=AMAPRRunResult)
async def trigger_rebalance():
    """Trigger the Agentic Multi-Asset Portfolio Rebalancer negotiation logic."""
    state = await amapr_service.get_portfolio()
    result = await amapr_service.run_rebalance("PF_001", state)
    return result

@router.get("/rwa-catalog")
async def get_rwa_catalog():
    """Get the catalog of tokenized real-world assets available for allocation."""
    return [
        {"id": "RE_TOKEN_A", "name": "Mumbai Commercial Real Estate", "type": "REAL_ESTATE", "apy": 0.08, "liquidity": "HIGH"},
        {"id": "PC_CREDIT_B", "name": "SME Private Credit Fund", "type": "PRIVATE_CREDIT", "apy": 0.12, "liquidity": "MEDIUM"}
    ]
