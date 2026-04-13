"""
FinSight — Macro Flow Agent.
Fetches BSE FII/DII activity and derives a market-wide macro signal.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import httpx
import pandas as pd
import numpy as np
import yfinance as yf

from backend.models.schemas import MacroResult

logger = logging.getLogger(__name__)

BSE_FIIDII_URL = "https://api.bseindia.com/BseIndiaAPI/api/FiiDii/w"

_DATE_KEYS = ("date", "tradeDate", "trade_date", "tradingDate")


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text or text in {"-", "--", "NA", "N/A", "null", "None"}:
        return None

    text = text.replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def _normalized_key(key: str) -> str:
    return "".join(ch for ch in str(key).lower() if ch.isalnum())


def _pick_float_by_tokens(row: dict[str, Any], required_tokens: tuple[str, ...]) -> float | None:
    for key, value in row.items():
        norm_key = _normalized_key(key)
        if all(token in norm_key for token in required_tokens):
            parsed = _to_float(value)
            if parsed is not None:
                return parsed
    return None


def _pick_date(row: dict[str, Any]) -> datetime | None:
    raw_date: Any = None
    for key in _DATE_KEYS:
        if key in row:
            raw_date = row.get(key)
            break

    if raw_date is None:
        return None

    date_text = str(raw_date).strip()
    if not date_text:
        return None

    for fmt in (
        "%d-%b-%Y",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%d %b %Y",
    ):
        try:
            return datetime.strptime(date_text, fmt)
        except ValueError:
            continue

    return None


def _extract_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        dict_rows = [row for row in payload if isinstance(row, dict)]
        return dict_rows

    if not isinstance(payload, dict):
        return []

    candidates: list[list[dict[str, Any]]] = []

    def walk(node: Any) -> None:
        if isinstance(node, list):
            dict_rows = [item for item in node if isinstance(item, dict)]
            if dict_rows:
                candidates.append(dict_rows)
            for item in node:
                walk(item)
            return
        if isinstance(node, dict):
            for value in node.values():
                walk(value)

    walk(payload)
    if not candidates:
        return []

    def score(rows: list[dict[str, Any]]) -> int:
        value = 0
        for row in rows:
            keys = {_normalized_key(k) for k in row.keys()}
            if any("date" in key for key in keys):
                value += 2
            if any("fii" in key for key in keys):
                value += 3
            if any("dii" in key for key in keys):
                value += 3
            if any("net" in key for key in keys):
                value += 2
        return value

    return max(candidates, key=score)


def _derive_daily_net(row: dict[str, Any], investor_prefix: str) -> float | None:
    net_value = _pick_float_by_tokens(row, (investor_prefix, "net"))
    if net_value is not None:
        return net_value

    buy_value = _pick_float_by_tokens(row, (investor_prefix, "buy"))
    if buy_value is None:
        buy_value = _pick_float_by_tokens(row, (investor_prefix, "purchase"))

    sell_value = _pick_float_by_tokens(row, (investor_prefix, "sell"))
    if sell_value is None:
        sell_value = _pick_float_by_tokens(row, (investor_prefix, "sale"))

    if buy_value is not None and sell_value is not None:
        return buy_value - sell_value

    return None


def _derive_trend(values: list[float]) -> str:
    if not values:
        return "mixed"
    if all(value > 0 for value in values):
        return "buying"
    if all(value < 0 for value in values):
        return "selling"
    return "mixed"


def _format_rupees(value: float | None) -> str:
    if value is None:
        return "NA"
    return f"{value:.2f}"


def parse_bse_fiidii(data: Any) -> dict[str, Any]:
    rows = _extract_rows(data)
    if not rows:
        raise ValueError("BSE FII/DII response had no rows")

    parsed_days: list[dict[str, Any]] = []
    for row in rows:
        fii_net = _derive_daily_net(row, "fii")
        dii_net = _derive_daily_net(row, "dii")
        if fii_net is None or dii_net is None:
            continue

        parsed_days.append(
            {
                "date": _pick_date(row),
                "fii_net": float(fii_net),
                "dii_net": float(dii_net),
            }
        )

    if not parsed_days:
        raise ValueError("BSE FII/DII response had no parseable rows")

    if any(day["date"] is not None for day in parsed_days):
        parsed_days.sort(
            key=lambda day: day["date"] or datetime.min,
            reverse=True,
        )

    recent_days = parsed_days[:5]
    latest_day = recent_days[0]

    fii_values = [day["fii_net"] for day in recent_days]
    dii_values = [day["dii_net"] for day in recent_days]

    latest_date = latest_day["date"]
    if isinstance(latest_date, datetime):
        date_str = latest_date.date().isoformat()
    else:
        date_str = datetime.now(timezone.utc).date().isoformat()

    return {
        "fii_net": float(latest_day["fii_net"]),
        "dii_net": float(latest_day["dii_net"]),
        "fii_5d_trend": _derive_trend(fii_values),
        "dii_5d_trend": _derive_trend(dii_values),
        "source": "BSE",
        "date": date_str,
        "fii_net_5d_total": round(sum(fii_values), 2),
        "dii_net_5d_total": round(sum(dii_values), 2),
    }


def _calculate_contagion_risk(shocks: dict[str, float]) -> tuple[float, list[str]]:
    """
    DCC-GARCH-inspired shock propagation logic.
    Maps global asset percentage changes to Indian sector vulnerabilities.
    """
    # Vulnerability Matrix: {sector: {macro_asset: correlation}}
    # These are stylized values for the Indian market
    vulnerability_matrix = {
        "FINANCIALS": {"US10Y": -0.4, "USDINR": -0.3, "OIL": -0.2},
        "IT": {"US10Y": -0.6, "USDINR": 0.5, "OIL": 0.1},
        "ENERGY": {"OIL": 0.8, "US10Y": -0.1, "USDINR": -0.2},
        "AUTO": {"OIL": -0.6, "USDINR": -0.4, "US10Y": -0.2},
        "PHARMA": {"USDINR": 0.4, "US10Y": -0.1, "OIL": 0.2},
    }
    
    sector_scores = {sector: 0.0 for sector in vulnerability_matrix}
    overall_risk = 0.0
    
    for asset, shock in shocks.items():
        impact_weight = abs(shock) / 2.0  # normalize
        for sector, corrs in vulnerability_matrix.items():
            if asset in corrs:
                # Shock propagation: change * correlation
                effect = shock * corrs[asset]
                sector_scores[sector] += effect
                overall_risk += abs(effect)
                
    # Normalize risk score to 0-10
    final_risk = min(10.0, overall_risk * 5.0)
    
    # Identify sectors with negative impact > 1%
    vulnerable = [s for s, score in sector_scores.items() if score < -0.01]
    
    return round(final_risk, 2), vulnerable


async def _fetch_global_shocks() -> dict[str, float]:
    """Fetch 5-day % change for key macro contagion drivers."""
    drivers = {
        "OIL": "BZ=F",    # Brent Crude
        "US10Y": "^TNX",  # US 10Y Yield
        "DXY": "DX-Y.NYB" # Dollar Index
    }
    
    shocks = {}
    for label, ticker in drivers.items():
        try:
            data = await asyncio.to_thread(yf.download, ticker, period="7d", progress=False)
            if not data.empty:
                closes = data["Close"]
                if isinstance(closes, pd.DataFrame):
                     closes = closes.iloc[:, 0]
                ret = (closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0] * 100
                shocks[label] = float(ret)
            else:
                shocks[label] = 0.0
        except Exception:
            shocks[label] = 0.0
            
    return shocks

def _compute_nifty_5d_return() -> float:
    nifty = yf.download("^NSEI", period="5d", interval="1d", progress=False)
    if nifty.empty:
        return 0.0

    frame = nifty.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = [str(column[0]) for column in frame.columns]

    if "Close" not in frame.columns:
        return 0.0

    closes = pd.to_numeric(frame["Close"], errors="coerce").dropna()
    if closes.shape[0] < 2:
        return 0.0

    first = float(closes.iloc[0])
    last = float(closes.iloc[-1])
    if first == 0:
        return 0.0

    return (last - first) / first * 100.0


async def fetch_macro_fallback() -> dict[str, Any]:
    try:
        five_day_return = await asyncio.to_thread(_compute_nifty_5d_return)
    except Exception:
        five_day_return = 0.0

    return {
        "fii_net": None,
        "dii_net": None,
        "fii_5d_trend": "unknown",
        "dii_5d_trend": "unknown",
        "source": "derived_from_index",
        "nifty_5d_return": round(five_day_return, 2),
        "macro_signal": (
            "bullish"
            if five_day_return > 1
            else "bearish"
            if five_day_return < -1
            else "neutral"
        ),
    }


async def fetch_macro_flow() -> dict[str, Any]:
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.bseindia.com"}
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(BSE_FIIDII_URL, headers=headers, timeout=10)
            r.raise_for_status()
            return parse_bse_fiidii(r.json())
        except Exception:
            return await fetch_macro_fallback()


async def fetch_macro_full() -> MacroResult:
    """Fetch FII/DII flow and Global Contagion data."""
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.bseindia.com"}
    flow_task = fetch_macro_flow()
    shock_task = _fetch_global_shocks()
    
    flow, shocks = await asyncio.gather(flow_task, shock_task)
    
    contagion_score, vulnerable = _calculate_contagion_risk(shocks)
    
    # Base result conversion
    res = _to_macro_result(flow)
    
    # Inject contagion mapper data
    res.contagion_risk_score = contagion_score
    res.vulnerable_sectors = vulnerable
    res.global_shocks = shocks
    
    # Adjust reasoning to include contagion notes
    shock_note = ", ".join([f"{k}: {v:+.1f}%" for k, v in shocks.items() if abs(v) > 0.5])
    if vulnerable:
        res.reasoning += f" | Contagion Risk: {contagion_score}/10 (Vulnerable: {', '.join(vulnerable)})"
    
    if shock_note:
        res.reasoning += f" | Global Shocks: {shock_note}"
        
    return res


def _to_macro_result(flow: dict[str, Any]) -> MacroResult:
    source = str(flow.get("source") or "derived_from_index")
    source_upper = source.upper()

    if source_upper == "BSE":
        fii_today = _to_float(flow.get("fii_net"))
        dii_today = _to_float(flow.get("dii_net"))

        fii_trend = str(flow.get("fii_5d_trend") or "mixed").lower()
        if fii_trend not in {"buying", "selling", "mixed"}:
            fii_trend = "mixed"

        dii_trend = str(flow.get("dii_5d_trend") or "mixed").lower()
        if dii_trend not in {"buying", "selling", "mixed"}:
            dii_trend = "mixed"

        trend_summary = (
            fii_trend
            if fii_trend == dii_trend
            else f"FII {fii_trend}, DII {dii_trend}"
        )

        if fii_trend == "buying":
            macro_signal = "BULLISH"
            confidence_multiplier = 1.1
        elif fii_trend == "selling":
            macro_signal = "BEARISH"
            confidence_multiplier = 0.9
        else:
            macro_signal = "NEUTRAL"
            confidence_multiplier = 1.0

        fii_net_5d = _to_float(flow.get("fii_net_5d_total"))
        dii_net_5d = _to_float(flow.get("dii_net_5d_total"))

        return MacroResult(
            fii_net_5d=round(fii_net_5d if fii_net_5d is not None else (fii_today or 0.0), 2),
            dii_net_5d=round(dii_net_5d if dii_net_5d is not None else (dii_today or 0.0), 2),
            macro_signal=macro_signal,
            confidence_multiplier=confidence_multiplier,
            reasoning=(
                f"[MACRO] FII net: \u20b9{_format_rupees(fii_today)}Cr | "
                f"DII net: \u20b9{_format_rupees(dii_today)}Cr \u2014 {trend_summary}"
            ),
            source="BSE",
            date=str(flow.get("date") or datetime.now(timezone.utc).date().isoformat()),
            fii_net=fii_today,
            dii_net=dii_today,
            dii_5d_trend=dii_trend,
            nifty_5d_return=None,
            is_demo=False,
        )

    nifty_5d_return = _to_float(flow.get("nifty_5d_return")) or 0.0
    macro_signal_raw = str(flow.get("macro_signal") or "neutral").lower()
    if macro_signal_raw == "bullish":
        macro_signal = "BULLISH"
        confidence_multiplier = 1.05
    elif macro_signal_raw == "bearish":
        macro_signal = "BEARISH"
        confidence_multiplier = 0.95
    else:
        macro_signal = "NEUTRAL"
        confidence_multiplier = 1.0

    return MacroResult(
        fii_net_5d=0.0,
        dii_net_5d=0.0,
        macro_signal=macro_signal,
        confidence_multiplier=confidence_multiplier,
        reasoning=(
            f"[MACRO] Exchange APIs unavailable. Nifty 5D: {nifty_5d_return:.2f}% "
            f"\u2014 {macro_signal_raw}"
        ),
        source="derived_from_index",
        date=datetime.now(timezone.utc).date().isoformat(),
        fii_net=None,
        dii_net=None,
        fii_5d_trend="unknown",
        dii_5d_trend="unknown",
        nifty_5d_return=round(nifty_5d_return, 2),
        is_demo=True,
    )


async def run() -> MacroResult:
    """Fetch BSE FII/DII activity and derive a macro flow signal."""
    try:
        result = await fetch_macro_full()
        logger.info(
            "macro: source=%s signal=%s fii_net_5d=%.2f dii_net_5d=%.2f multiplier=%.2f",
            result.source,
            result.macro_signal,
            result.fii_net_5d,
            result.dii_net_5d,
            result.confidence_multiplier,
        )
        return result
    except Exception as exc:
        logger.error("Macro agent failed: %s", exc)
        fallback = await fetch_macro_fallback()
        return _to_macro_result(fallback)
