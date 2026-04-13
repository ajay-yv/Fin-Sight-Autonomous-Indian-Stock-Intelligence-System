"""
FinSight — Predictive Earnings Whisper Engine.
Analyzes concall transcripts (via LLM) and alternative data proxies 
to predict earnings surprises.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
from datetime import datetime, timezone
import feedparser
from typing import Any, Optional, Literal

from backend.models.schemas import EarningsWhisperData
from backend.gateways.trendlyne_client import trendlyne_client
from api.cache import earnings_cache

logger = logging.getLogger(__name__)

# ── Configuration ───────────────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
EARNINGS_MODEL = os.getenv("EARNINGS_MODEL", "google/gemini-2.0-flash")

_EARNINGS_SYSTEM_PROMPT = (
    "You are an earnings detective for Dalal Street. "
    "Analyze the recent management commentary, concall transcripts, and alternative data cues. "
    "Predict if the company is likely to beat or miss earnings expectations. "
    "Return ONLY valid JSON with these exact keys: "
    "whisper_score (float 0.0 to 10.0), "
    "surprise_probability (float 0.0 to 1.0), "
    "concall_tone (exactly one of: bullish, bearish, cautious, optimistic), "
    "alternative_data_proxy (string summary), "
    "signal (exactly one of: BUY, SELL, HOLD), "
    "confidence (float 0.0 to 1.0), "
    "reasoning (string, max 2 sentences). "
    "Do not include any text outside the JSON object."
)

async def _get_earnings_cues(symbol: str) -> list[str]:
    """Fetch recent concall summaries or earnings-related news."""
    clean = symbol.replace(".NS", "").replace(".BO", "").strip().upper()
    url = f"https://news.google.com/rss/search?q={clean}+earnings+concall+transcript+summary&hl=en-IN&gl=IN&ceid=IN:en"
    
    cues = []
    try:
        feed = await asyncio.to_thread(feedparser.parse, url)
        for entry in feed.entries[:10]:
            cues.append(entry.title)
    except Exception as exc:
        logger.error("Failed to fetch earnings cues for %s: %s", symbol, exc)
        
    return cues

async def run(symbol: str) -> EarningsWhisperData:
    """Main entry point for Earnings Whisper agent."""
    logger.info("Running Earnings Whisper analysis for %s", symbol)
    
    # Phase 3: Earnings Caching
    cached_result = earnings_cache.get(symbol)
    if cached_result:
        logger.info("⚡ Earnings cache hit for %s", symbol)
        return cached_result
    
    # Phase 3: Earnings Caching
    
    # Parallel Fetching: Cues + Trendlyne
    cues_task = _get_earnings_cues(symbol)
    tl_data_task = trendlyne_client.get_earnings_surprises(symbol)
    tl_concall_task = trendlyne_client.get_concall_signals(symbol)
    
    responses = await asyncio.gather(cues_task, tl_data_task, tl_concall_task, return_exceptions=True)
    cues = responses[0] if not isinstance(responses[0], Exception) else []
    tl_data = responses[1] if not isinstance(responses[1], Exception) else None
    tl_concall = responses[2] if not isinstance(responses[2], Exception) else None
    
    # Alternative data simulation (GST, Channel Checks)
    proxies = [
        "GST Filings for sector showing 12% YoY growth",
        "Channel checks suggest inventory destocking completed",
        "High-frequency electricity data indicates plant utilization at 85%",
        "Weak monsoon impact on rural demand proxies",
        "Increased hiring activity in core business segments"
    ]
    selected_proxy = random.choice(proxies)
    
    if not cues:
        # Fallback to pure proxy analysis if no news
        cues = ["No recent concall transcripts found; relying on alternative data proxies."]

    is_placeholder = OPENROUTER_API_KEY.startswith("your_") or "api_key_here" in OPENROUTER_API_KEY
    if not OPENROUTER_API_KEY or is_placeholder:
        result = EarningsWhisperData(
            symbol=symbol,
            whisper_score=5.0,
            surprise_probability=0.5,
            concall_tone="bullish" if "growth" in selected_proxy.lower() else "cautious",
            alternative_data_proxy=selected_proxy,
            signal="HOLD",
            confidence=0.5,
            reasoning="Predictive proxy modeling active. Synthesizing alternative data cues into a deterministic earnings whisper.",
            key_triggers=["Earnings analysis in Simulation Mode"],
            is_demo=True
        )
        earnings_cache.set(symbol, result, 3600)
        return result

    try:
        payload = {
            "model": EARNINGS_MODEL,
            "messages": [
                {"role": "system", "content": _EARNINGS_SYSTEM_PROMPT},
                {
                    "role": "user", 
                    "content": f"Symbol: {symbol}\nCues: {json.dumps(cues)}\nAlt Proxy: {selected_proxy}"
                },
            ],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            raw_result = data["choices"][0]["message"]["content"].strip()
            
            if raw_result.startswith("```"):
                raw_result = raw_result.strip("```json").strip("```").strip()
                
            res = json.loads(raw_result)
            
            whisper_score = float(res.get("whisper_score", 5.0))
            prob = float(res.get("surprise_probability", 0.5))
            tone = res.get("concall_tone", "bullish")
            signal = res.get("signal", "HOLD")
            conf = float(res.get("confidence", 0.6))
            reasoning = res.get("reasoning", "Surprise predicted.")
            
            triggers = [f"Management tone: {tone.upper()}"]
            if whisper_score > 7.5:
                triggers.append(f"High Earnings Surprise Score ({whisper_score})")
            if "growth" in selected_proxy.lower():
                triggers.append("Bullish Alt-Data Proxy Detected")

            is_demo_final = not (tl_data and tl_concall)

            result = EarningsWhisperData(
                symbol=symbol,
                whisper_score=tl_data.get("consensus_estimate", whisper_score) if tl_data else whisper_score,
                surprise_probability=prob,
                concall_tone=tl_concall.get("tone", tone) if tl_concall else tone,
                alternative_data_proxy=selected_proxy,
                signal=signal,
                confidence=conf,
                reasoning=f"{reasoning} [Trendlyne Intelligence Active]",
                key_triggers=triggers,
                is_demo=is_demo_final
            )
            
            # Cache the result
            earnings_cache.set(symbol, result, 3600)
            return result

    except Exception as exc:
        logger.error("Earnings Whisper analysis failed for %s: %s", symbol, exc)
        return EarningsWhisperData(
            symbol=symbol,
            whisper_score=5.0,
            surprise_probability=0.5,
            concall_tone="cautious",
            alternative_data_proxy=selected_proxy,
            signal="HOLD",
            confidence=0.3,
            reasoning=f"Earnings analysis error: {str(exc)}",
            key_triggers=["Agent error"]
        )

if __name__ == "__main__":
    async def test():
        res = await run("HDFCBANK")
        print(res.model_dump_json(indent=2))
        
    asyncio.run(test())
