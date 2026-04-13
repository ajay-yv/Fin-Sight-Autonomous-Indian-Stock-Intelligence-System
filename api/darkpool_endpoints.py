from fastapi import APIRouter, HTTPException
from typing import Dict, List
from backend.services.darkpool.darkpool_service import DarkPoolService

router = APIRouter(prefix="/api/darkpool", tags=["Dark Pool"])
darkpool_service = DarkPoolService()

@router.post("/order")
async def place_private_order(symbol: str, side: str, quantity: float):
    """
    Submits a privacy-preserving order to the decentralized dark pool.
    """
    result = await darkpool_service.submit_private_order(symbol, side, quantity)
    return result

@router.get("/stats")
async def get_darkpool_stats():
    """
    Retrieve aggregate stats of the dark pool volume (without revealing individual trades).
    """
    return {
        "confidential_volume": darkpool_service.get_market_volume(),
        "active_enclaves": 3,
        "protocol_version": "v2.0-2026-confidential"
    }

@router.get("/signals")
async def get_institutional_signals(symbol: str):
    """
    Fetches real-world institutional signals for the given symbol.
    """
    return await darkpool_service.get_institutional_signals(symbol)

@router.get("/trades")
async def get_my_recent_trades():
    """
    In a real system, this would requires Auth and only show the user's trades.
    For the prototype, it shows the history of the matched matches.
    """
    return darkpool_service.trades_history
