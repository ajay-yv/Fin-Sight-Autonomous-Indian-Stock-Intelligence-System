"""
FinSight — Dalal Street Social Pulse Agent.
Ingests multi-source social sentiment (Telegram, Reddit, X) and processes 
Hinglish financial slang using a specialized LLM prompt.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Optional
from datetime import datetime, timezone

import feedparser
import httpx

from backend.models.schemas import SocialPulseData

logger = logging.getLogger(__name__)

# ── Configuration ───────────────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
SOCIAL_PULSE_MODEL = os.getenv("SOCIAL_PULSE_MODEL", "google/gemini-2.0-flash")

_SOCIAL_SYSTEM_PROMPT = (
    "You are a specialist in Indian retail stock market sentiment. "
    "You understand Dalal Street jargon, Hinglish slang (e.g., 'to the moon', 'operator game', 'paisa double'), "
    "and retail crowd emotions. Analyze the provided social media snippets. "
    "Return ONLY valid JSON with these exact keys: "
    "social_score (float -1.0 to 1.0), "
    "volume_spike_flag (boolean), "
    "sentiment_label (exactly one of: positive, negative, neutral), "
    "dominant_platform (e.g., Telegram, Reddit, X), "
    "top_keywords (array of 3-5 keywords), "
    "signal (exactly one of: BUY, SELL, HOLD), "
    "confidence (float 0.0 to 1.0), "
    "reasoning (string, max 2 sentences). "
    "Do not include any text outside the JSON object."
)

def _get_social_pulse_feeds(symbol: str) -> list[str]:
    """
    Fetch social mentions via Google News RSS search proxies for Reddit, Telegram, etc.
    """
    clean = symbol.replace(".NS", "").replace(".BO", "").strip().upper()
    
    # Targeting social platforms specifically
    queries = [
        f"{clean}+Reddit+r/IndiaInvestments",
        f"{clean}+Telegram+Dalal+Street",
        f"{clean}+X.com+stock+market",
    ]
    
    mentions = []
    for query in queries:
        url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                mentions.append(f"[{query.split('+')[1]}] {entry.title}")
        except Exception as exc:
            logger.error("Failed to fetch social pulse for %s query %s: %s", symbol, query, exc)
            
    return mentions

async def _analyze_social_tone(symbol: str, mentions: list[str]) -> str:
    """Analyze social mentions via LLM."""
    payload = {
        "model": SOCIAL_PULSE_MODEL,
        "messages": [
            {"role": "system", "content": _SOCIAL_SYSTEM_PROMPT},
            {
                "role": "user", 
                "content": f"Symbol: {symbol}\nSocial Mentions: {json.dumps(mentions)}"
            },
        ],
        "temperature": 0.3,
        "max_tokens": 500,
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
        return data["choices"][0]["message"]["content"].strip()

async def run(symbol: str) -> SocialPulseData:
    """Entry point for Social Pulse Agent."""
    logger.info("Running Social Pulse Agent for %s", symbol)
    
    mentions = _get_social_pulse_feeds(symbol)
    
    if not mentions:
        return SocialPulseData(
            symbol=symbol,
            social_score=0.0,
            volume_spike_flag=False,
            dominant_platform="None",
            top_keywords=[],
            sentiment_label="neutral",
            signal="HOLD",
            confidence=0.4,
            reasoning="Low social discussion volume detected across major platforms.",
            key_triggers=["Thin social buzz"]
        )

    if not OPENROUTER_API_KEY:
         return SocialPulseData(
            symbol=symbol,
            social_score=0.0,
            volume_spike_flag=False,
            dominant_platform="Unknown",
            top_keywords=[],
            sentiment_label="neutral",
            signal="HOLD",
            confidence=0.0,
            reasoning="OpenRouter API key missing — social analysis unavailable.",
            key_triggers=[]
        )

    try:
        raw_result = await _analyze_social_tone(symbol, mentions)
        
        # Clean markdown fences
        if raw_result.startswith("```"):
            raw_result = raw_result.strip("```json").strip("```").strip()
            
        res = json.loads(raw_result)
        
        score = float(res.get("social_score", 0.0))
        spike = bool(res.get("volume_spike_flag", False))
        label = res.get("sentiment_label", "neutral")
        platform = res.get("dominant_platform", "Reddit")
        keywords = res.get("top_keywords", [])
        signal = res.get("signal", "HOLD")
        confidence = float(res.get("confidence", 0.6))
        reasoning = res.get("reasoning", "Social sentiment processed.")
        
        triggers = [f"Social buzz detected primarily on {platform}"]
        if spike:
            triggers.append("Retail volume spike/chatter alert")
        if abs(score) > 0.6:
            triggers.append(f"Strong social polarization ({label})")
            
        return SocialPulseData(
            symbol=symbol,
            social_score=score,
            volume_spike_flag=spike,
            dominant_platform=platform,
            top_keywords=keywords,
            sentiment_label=label,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            key_triggers=triggers
        )
        
    except Exception as exc:
        logger.error("Social Pulse LLM failure for %s: %s", symbol, exc)
        return SocialPulseData(
            symbol=symbol,
            social_score=0.0,
            volume_spike_flag=False,
            dominant_platform="Error",
            top_keywords=[],
            sentiment_label="neutral",
            signal="HOLD",
            confidence=0.2,
            reasoning=f"Social analysis failed: {str(exc)}",
            key_triggers=["Agent error"]
        )

if __name__ == "__main__":
    async def test():
        load_dotenv()
        result = await run("RELIANCE")
        print(result.model_dump_json(indent=2))
        
    from dotenv import load_dotenv
    asyncio.run(test())
