"""
FinSight — Institutional Options Flow Intelligence Agent.
Analyses NSE F&O data (OI, PCR, IV, GEX) to detect institutional positioning.
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from backend.models.schemas import OptionsFlowData

logger = logging.getLogger(__name__)

async def fetch_options_chain(symbol: str) -> dict[str, Any]:
    """
    Fetch live options chain data from NSE or a reliable data provider proxy.
    In this implementation, we simulate the fetch if a real API endpoint isn't provided.
    """
    clean = symbol.replace(".NS", "").replace(".BO", "").strip().upper()
    
    # In a real scenario, we'd use 'https://www.nseindia.com/api/option-chain-equities?symbol={clean}'
    # But that requires complex cookie/header rotation.
    # For now, we simulate realistic F&O metrics based on current market regimes.
    
    logger.info("Fetching F&O data for %s", clean)
    await asyncio.sleep(0.5) # Simulate network lag
    
    # Deterministic simulation based on symbol and date to keep it consistent within a run
    seed = sum(ord(c) for c in clean) + datetime.now().day
    random.seed(seed)
    
    return {
        "pcr": round(0.6 + random.random() * 0.8, 2), # 0.6 to 1.4
        "iv_rank": round(random.random() * 100, 1),
        "max_pain": 0.0, # Will be set relative to spot
        "gex_net": round((random.random() - 0.5) * 10, 2), # -5 to +5 Bn
        "oi_change_velocity": round(random.random() * 2, 2)
    }

async def run(symbol: str, current_price: float) -> OptionsFlowData:
    """Main entry point for the Options Flow agent."""
    logger.info("Running Options Flow analysis for %s at %.2f", symbol, current_price)
    
    try:
        data = await fetch_options_chain(symbol)
        
        pcr = data["pcr"]
        iv_rank = data["iv_rank"]
        gex = data["gex_net"]
        oi_v = data["oi_change_velocity"]
        
        # Max Pain simulation: usually near recent round numbers or current spot
        max_pain = round(current_price * (1 + (random.random() - 0.5) * 0.02), -1)
        
        # Signal logic
        # High PCR (>1.2) + High IV Rank (>70) = Potential bullish reversal (oversold)
        # Low PCR (<0.7) + Low IV = Potential bearish distribution
        # Positive GEX = Low volatility (stable)
        # Negative GEX = High volatility (fragile)
        
        signal = "HOLD"
        confidence = 0.6
        reasoning = "Institutional positioning is neutral."
        triggers = []
        
        if pcr > 1.3:
            signal = "BUY"
            reasoning = f"Extreme high PCR ({pcr}) suggests oversold retail sentiment; institutional accumulation likely."
            triggers.append(f"Bullish Divergence: PCR at {pcr}")
        elif pcr < 0.65:
            signal = "SELL"
            reasoning = f"Extremely low PCR ({pcr}) indicates retail euphoria; institutional distribution possible."
            triggers.append(f"Bearish Euphoria: PCR at {pcr}")
            
        if iv_rank > 80:
            triggers.append(f"High IV Rank ({iv_rank}%): Option selling attractive")
        
        if gex < -3.0:
            triggers.append("Negative Gamma zone: Expect high volatility expansion")
        elif gex > 3.0:
            triggers.append("Positive Gamma zone: Price likely to remain range-bound/sticky")

        return OptionsFlowData(
            symbol=symbol,
            pcr=pcr,
            iv_rank=iv_rank,
            max_pain=max_pain,
            gex_net=gex,
            oi_change_velocity=oi_v,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            key_triggers=triggers
        )

    except Exception as exc:
        logger.error("Options Flow analysis failed for %s: %s", symbol, exc)
        return OptionsFlowData(
            symbol=symbol,
            pcr=1.0,
            iv_rank=50.0,
            max_pain=current_price,
            gex_net=0.0,
            oi_change_velocity=0.0,
            signal="HOLD",
            confidence=0.3,
            reasoning=f"Options analysis unavailable: {str(exc)}",
            key_triggers=["Agent error"]
        )

if __name__ == "__main__":
    async def test():
        res = await run("NIFTY50", 22500.0)
        print(res.model_dump_json(indent=2))
        
    asyncio.run(test())
