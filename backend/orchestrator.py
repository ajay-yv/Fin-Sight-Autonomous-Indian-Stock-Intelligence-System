"""
FinSight — Orchestrator.
Coordinates all specialist agents for each analysis run and persists
intermediate outputs for real-time SSE streaming.
"""

from __future__ import annotations

import asyncio
import logging
import traceback

from backend.agents import (
    critic,
    data_ingestion,
    eda_agent,
    fundamental,
    earnings_agent,
    macro_agent,
    ml_agent,
    options_flow_agent,
    regulatory_agent,
    risk,
    sentiment,
    social_pulse_agent,
    synthesis,
    technical,
)
from backend.database import save_agent_output, save_synthesis_result, update_run_status
from backend.models.schemas import MLPrediction, MacroResult, ModelMetrics, OHLCVData, RiskMetrics, SentimentData
from backend.context import IntelligenceContext

logger = logging.getLogger(__name__)

_CARD_AGENT_WEIGHTS: dict[str, float] = {
    "technical": 0.22,
    "fundamental": 0.30,
    "sentiment": 0.13,
    "risk": 0.20,
    "ml_prediction": 0.15,
    "regulatory": 0.10,
    "social_pulse": 0.07,
    "options_flow": 0.13,
    "earnings": 0.12,
    "synthesis": 1.0,
}


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────
def _update_progress(run_id: str, symbol: str, agent_name: str, status: str) -> None:
    """Log progress and potentially update DB (stub for future granular tracking)."""
    logger.info("[%s] %s: %s", symbol, agent_name, status)

def _save_success(run_id: str, symbol: str, agent_name: str, result) -> None:
    """Persist a successful agent output to the database."""
    signal = getattr(result, "signal", None)
    confidence = getattr(result, "confidence", None)
    if confidence is None:
        confidence = getattr(result, "prediction_confidence", None)
    reasoning = getattr(result, "reasoning", None)

    if agent_name == "synthesis":
        signal = getattr(result, "final_verdict", None)
        confidence = getattr(result, "overall_confidence", None)

    if agent_name == "data_ingestion":
        signal = None
        confidence = None
        reasoning = (
            f"Fetched {len(result.dates)} days of data. "
            f"Current: Rs.{result.current_price} ({result.change_pct:+.2f}%)"
        )
    elif agent_name == "eda":
        signal = None
        confidence = None
        reasoning = (
            f"Generated multi-stock EDA for {len(getattr(result, 'symbols', []))} symbols."
        )
    elif agent_name == "critic":
        signal = None
        confidence = getattr(result, "confidence_penalty", None)
        challenges = getattr(result, "challenges", []) or []
        reasoning = (
            "All agents in agreement with sufficient confidence."
            if not challenges
            else "Critic challenges: " + " | ".join(challenges[:3])
        )
    elif agent_name == "macro":
        macro_signal = getattr(result, "macro_signal", None)
        signal = {
            "BULLISH": "BUY",
            "BEARISH": "SELL",
            "NEUTRAL": "HOLD",
        }.get(macro_signal)
        confidence = None
    elif agent_name == "ml_prediction":
        model_valid = bool(getattr(result, "model_valid", True))
        if not model_valid:
            signal = None
            suppression_reason = getattr(result, "suppression_reason", None)
            if isinstance(suppression_reason, str) and suppression_reason.strip():
                reasoning = suppression_reason.strip()

    # Defensive serialization
    if hasattr(result, "model_dump"):
        data_dict = result.model_dump(mode="json")
    elif hasattr(result, "dict"):
        data_dict = result.dict()
    else:
        data_dict = None

    if isinstance(data_dict, dict) and agent_name in _CARD_AGENT_WEIGHTS:
        verdict = str(data_dict.get("verdict") or data_dict.get("signal") or signal or "HOLD").upper()

        if agent_name == "risk":
            risk_level = str(data_dict.get("risk_level", "MEDIUM")).upper()
            verdict = {"LOW": "BUY", "MEDIUM": "HOLD", "HIGH": "SELL"}.get(risk_level, "HOLD")
        elif agent_name == "ml_prediction" and not bool(getattr(result, "model_valid", True)):
            verdict = "INSUFFICIENT_DATA"

        if verdict not in {"BUY", "HOLD", "SELL", "INSUFFICIENT_DATA"}:
            verdict = "HOLD"

        if agent_name == "ml_prediction":
            raw_confidence = data_dict.get("prediction_confidence", confidence)
        else:
            raw_confidence = data_dict.get("confidence", confidence)

        try:
            normalized_confidence = float(raw_confidence if raw_confidence is not None else 0.0)
        except (TypeError, ValueError):
            normalized_confidence = 0.0
        normalized_confidence = max(0.0, min(1.0, normalized_confidence))

        score = float(round(normalized_confidence * 10.0, 2))
        if agent_name == "risk":
            risk_level = str(data_dict.get("risk_level", "MEDIUM")).upper()
            score = float({"LOW": 8, "MEDIUM": 5, "HIGH": 2}.get(risk_level, 5))
        elif agent_name == "ml_prediction":
            override_score = data_dict.get("score_override")
            if isinstance(override_score, (int, float)):
                score = float(override_score)

        score = max(0.0, min(10.0, score))

        weight = _CARD_AGENT_WEIGHTS[agent_name]
        if agent_name == "ml_prediction":
            override_weight = data_dict.get("weight_override")
            if isinstance(override_weight, (int, float)):
                weight = float(override_weight)
        weight = max(0.0, min(1.0, float(weight)))

        raw_triggers = data_dict.get("triggers")
        if not isinstance(raw_triggers, list):
            raw_triggers = data_dict.get("key_triggers")
        triggers = [
            str(item).strip() for item in (raw_triggers or []) if str(item).strip()
        ]

        weighted_score = round(score * weight, 4)

        data_dict["agent"] = agent_name
        data_dict["verdict"] = verdict
        data_dict["score"] = score
        data_dict["weight"] = weight
        data_dict["weighted_score"] = weighted_score
        data_dict["triggers"] = triggers
        data_dict["confidence"] = normalized_confidence

    save_agent_output(
        run_id=run_id,
        symbol=symbol,
        agent_name=agent_name,
        status="completed",
        signal=signal,
        confidence=confidence,
        reasoning=reasoning,
        data_dict=data_dict,
    )


def _save_failure(run_id: str, symbol: str, agent_name: str, error: str) -> None:
    """Persist a failed agent output to the database."""
    save_agent_output(
        run_id=run_id,
        symbol=symbol,
        agent_name=agent_name,
        status="failed",
        signal=None,
        confidence=None,
        reasoning=f"Agent failed: {error}",
        data_dict=None,
    )


def _mark_symbol_downstream_failed(run_id: str, symbol: str, reason: str) -> None:
    """Mark all downstream per-symbol agents as failed."""
    downstream_agents = (
        "technical",
        "fundamental",
        "sentiment",
        "risk",
        "macro",
        "ml_prediction",
        "regulatory",
        "social_pulse",
        "options_flow",
        "earnings",
        "synthesis",
        "critic",
    )
    for agent_name in downstream_agents:
        _save_failure(run_id, symbol, agent_name, reason)


# ──────────────────────────────────────────────────────────────────────
# Run stages
# ──────────────────────────────────────────────────────────────────────
async def _run_data_ingestion_stage(
    run_id: str,
    symbols: list[str],
) -> dict[str, IntelligenceContext]:
    """
    Stage 1 (parallel): fetch OHLCV and Ticker Metadata for each symbol.
    """
    context_dict: dict[str, IntelligenceContext] = {}

    async def _fetch_one(symbol: str) -> None:
        try:
            _update_progress(run_id, symbol, "data_ingestion", "running")
            context = await data_ingestion.run(symbol)
            context_dict[symbol] = context
            _save_success(run_id, symbol, "data_ingestion", context.ohlcv)
            logger.info("✓ %s data_ingestion complete", symbol)
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            logger.error("✗ %s data_ingestion FAILED: %s", symbol, error_msg)
            _save_failure(run_id, symbol, "data_ingestion", error_msg)
            # Cascade failure
            _mark_symbol_downstream_failed(
                run_id,
                symbol,
                f"Skipped - data ingestion failed: {error_msg}",
            )

    await asyncio.gather(*[_fetch_one(s) for s in symbols])
    return context_dict


async def _run_eda_and_ml_stage(
    run_id: str,
    symbols: list[str],
    context_dict: dict[str, IntelligenceContext],
) -> dict[str, MLPrediction | None]:
    """
    Stage 2 (parallel):
    1) Run multi-stock EDA once for the run and persist as agent output "eda".
    2) Run per-symbol ML predictions and persist each as "ml_prediction".
    """
    ml_predictions: dict[str, MLPrediction | None] = {symbol: None for symbol in symbols}

    async def _run_eda() -> None:
        try:
            ohlcv_dict = {s: context_dict[s].ohlcv for s in symbols if s in context_dict}
            eda_result = await eda_agent.run(run_id, symbols, ohlcv_dict)
            # Run-level output row uses symbol="ALL".
            _save_success(run_id, "ALL", "eda", eda_result)
            logger.info("✓ run %s eda complete (%d symbols)", run_id, len(symbols))
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            logger.error("✗ run %s eda FAILED: %s", run_id, error_msg)
            _save_failure(run_id, "ALL", "eda", error_msg)

    async def _run_ml_batch() -> None:
        ml_tasks = [
            ml_agent.run(symbol, context_dict[symbol])
            for symbol in symbols if symbol in context_dict
        ]
        ml_results = await asyncio.gather(*ml_tasks, return_exceptions=True)

        for symbol, ml_result in zip(symbols, ml_results):
            if isinstance(ml_result, Exception):
                error_msg = f"{type(ml_result).__name__}: {ml_result}"
                logger.error("✗ %s ml_prediction FAILED: %s", symbol, error_msg)
                _save_failure(run_id, symbol, "ml_prediction", error_msg)
                continue

            ml_predictions[symbol] = ml_result
            _save_success(run_id, symbol, "ml_prediction", ml_result)
            logger.info(
                "✓ %s ml_prediction: %s (%.0f%%)",
                symbol,
                ml_result.signal,
                ml_result.prediction_confidence * 100,
            )

    await asyncio.gather(_run_eda(), _run_ml_batch())
    return ml_predictions


async def _run_macro_stage(
    run_id: str,
    symbols: list[str],
) -> dict[str, MacroResult | None]:
    """
    Stage 2b: fetch run-level macro flow (NSE FII/DII) once,
    then persist the same macro output per symbol for UI consistency.
    """
    macro_by_symbol: dict[str, MacroResult | None] = {symbol: None for symbol in symbols}

    try:
        macro_result = await macro_agent.run()
        for symbol in symbols:
            macro_by_symbol[symbol] = macro_result
            _save_success(run_id, symbol, "macro", macro_result)

        logger.info(
            "✓ macro stage: signal=%s fii_net_5d=%.2f dii_net_5d=%.2f multiplier=%.2f",
            macro_result.macro_signal,
            macro_result.fii_net_5d,
            macro_result.dii_net_5d,
            macro_result.confidence_multiplier,
        )
    except Exception as exc:
        error_msg = f"{type(exc).__name__}: {exc}"
        logger.error("✗ macro stage FAILED: %s", error_msg)
        for symbol in symbols:
            _save_failure(run_id, symbol, "macro", error_msg)

    return macro_by_symbol


async def _run_symbol_analysis_stage(
    run_id: str,
    symbol: str,
    context: IntelligenceContext,
    ml_prediction: MLPrediction | None,
    macro_result: MacroResult | None,
) -> None:
    """
    Stage 3 (per symbol):
    technical + fundamental + sentiment + risk in parallel,
    followed by synthesis with ML + macro context.

    Stage 3.5 (per symbol):
    critic review when at least one agent disagrees with the final verdict.
    """
    tech_result = None
    fund_result = None
    sent_result = None
    risk_result = None
    reg_result = None
    social_result = None
    options_result = None
    earnings_result = None

    async def _run_regulatory() -> None:
        nonlocal reg_result
        try:
            reg_result = await regulatory_agent.run(symbol)
            _save_success(run_id, symbol, "regulatory", reg_result)
            logger.info("✓ %s regulatory: score=%.1f", symbol, reg_result.max_risk_score)
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            logger.error("✗ %s regulatory FAILED: %s", symbol, error_msg)
            _save_failure(run_id, symbol, "regulatory", error_msg)

    async def _run_social_pulse() -> None:
        nonlocal social_result
        try:
            social_result = await social_pulse_agent.run(symbol)
            _save_success(run_id, symbol, "social_pulse", social_result)
            logger.info("✓ %s social_pulse: score=%.2f", symbol, social_result.social_score)
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            logger.error("✗ %s social_pulse FAILED: %s", symbol, error_msg)
            _save_failure(run_id, symbol, "social_pulse", error_msg)

    async def _run_options_flow() -> None:
        nonlocal options_result
        try:
            options_result = await options_flow_agent.run(symbol, context.ohlcv.current_price)
            _save_success(run_id, symbol, "options_flow", options_result)
            logger.info("✓ %s options_flow: signal=%s", symbol, options_result.signal)
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            logger.error("✗ %s options_flow FAILED: %s", symbol, error_msg)
            _save_failure(run_id, symbol, "options_flow", error_msg)

    async def _run_earnings() -> None:
        nonlocal earnings_result
        try:
            earnings_result = await earnings_agent.run(symbol)
            _save_success(run_id, symbol, "earnings", earnings_result)
            logger.info("✓ %s earnings: whisper=%s", symbol, earnings_result.whisper_score)
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            logger.error("✗ %s earnings FAILED: %s", symbol, error_msg)
            _save_failure(run_id, symbol, "earnings", error_msg)

    async def _run_technical() -> None:
        nonlocal tech_result
        try:
            tech_result = await technical.run(symbol, context)
            _save_success(run_id, symbol, "technical", tech_result)
            logger.info("✓ %s technical: %s (%.0f%%)", symbol, tech_result.signal, tech_result.confidence * 100)
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            logger.error("✗ %s technical FAILED: %s", symbol, error_msg)
            _save_failure(run_id, symbol, "technical", error_msg)

    async def _run_fundamental() -> None:
        nonlocal fund_result
        try:
            fund_result = await fundamental.run(symbol, context)
            _save_success(run_id, symbol, "fundamental", fund_result)
            logger.info("✓ %s fundamental: %s (%.0f%%)", symbol, fund_result.signal, fund_result.confidence * 100)
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            logger.error("✗ %s fundamental FAILED: %s", symbol, error_msg)
            _save_failure(run_id, symbol, "fundamental", error_msg)

    async def _run_sentiment() -> None:
        nonlocal sent_result
        try:
            sent_result = await sentiment.run(symbol, context)
            _save_success(run_id, symbol, "sentiment", sent_result)
            logger.info("✓ %s sentiment: %s (%.0f%%)", symbol, sent_result.signal, sent_result.confidence * 100)
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            logger.error("✗ %s sentiment FAILED: %s", symbol, error_msg)
            _save_failure(run_id, symbol, "sentiment", error_msg)

    async def _run_risk() -> None:
        nonlocal risk_result
        try:
            risk_result = await risk.run(symbol, context)
            _save_success(run_id, symbol, "risk", risk_result)
            logger.info("✓ %s risk: %s (beta=%.2f)", symbol, risk_result.risk_level, risk_result.beta)
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            logger.error("✗ %s risk FAILED: %s", symbol, error_msg)
            _save_failure(run_id, symbol, "risk", error_msg)

    await asyncio.gather(
        _run_technical(),
        _run_fundamental(),
        _run_sentiment(),
        _run_risk(),
        _run_regulatory(),
        _run_social_pulse(),
        _run_options_flow(),
        _run_earnings(),
    )

    # Require at least technical and fundamental for synthesis
    if tech_result is None or fund_result is None:
        missing: list[str] = []
        if tech_result is None:
            missing.append("technical")
        if fund_result is None:
            missing.append("fundamental")
        error_msg = f"Cannot synthesise - missing critical agent outputs: {', '.join(missing)}"
        logger.warning("⚠ %s synthesis SKIPPED: %s", symbol, error_msg)
        _save_failure(run_id, symbol, "synthesis", error_msg)
        return

    # Create fallback stubs for any missing non-critical agents
    _sent_result = sent_result or SentimentData(
        symbol=symbol,
        headlines=[],
        sentiment_score=0.0,
        sentiment_label="neutral",
        key_themes=["data unavailable"],
        signal="HOLD",
        confidence=0.3,
        reasoning="Sentiment analysis unavailable — using neutral fallback.",
    )
    _risk_result = risk_result or RiskMetrics(
        symbol=symbol,
        beta=1.0,
        var_95=-0.02,
        sharpe_ratio=0.0,
        max_drawdown=-0.15,
        volatility_annualized=0.25,
        risk_level="MEDIUM",
        reasoning="Risk agent unavailable — using moderate default.",
        key_triggers=["Risk data unavailable"],
    )
    _ml_prediction = ml_prediction or MLPrediction(
        symbol=symbol,
        prediction_horizon="5-day direction",
        regime="sideways",
        predicted_direction="SIDEWAYS",
        prediction_confidence=0.4,
        feature_importances=[],
        model_metrics=ModelMetrics(
            accuracy=0.0,
            precision=0.0,
            recall=0.0,
            f1_score=0.0,
            confusion_matrix=[[0, 0, 0], [0, 0, 0], [0, 0, 0]],
            class_labels=["DOWN", "SIDEWAYS", "UP"],
            training_samples=0,
            test_samples=0,
        ),
        model_name="Unavailable",
        feature_count=0,
        signal="HOLD",
        reasoning="ML prediction unavailable — using neutral fallback.",
        key_triggers=[
            "ML prediction unavailable — suppression applied; excluded from composite score"
        ],
        verdict="INSUFFICIENT_DATA",
        model_valid=False,
        suppression_reason="ML prediction unavailable — suppression applied.",
        weight_override=0.0,
        score_override=5,
    )
    _macro_result = macro_result or MacroResult(
        fii_net_5d=0.0,
        dii_net_5d=0.0,
        macro_signal="NEUTRAL",
        confidence_multiplier=1.0,
        reasoning="Macro data unavailable — using neutral fallback.",
    )

    _reg_result = reg_result or RegulatoryData(
        symbol=symbol,
        events=[],
        max_risk_score=0.0,
        sentiment_impact="neutral",
        signal="HOLD",
        confidence=0.3,
        reasoning="Regulatory agent unavailable — using fallback.",
        key_triggers=["Data ingestion failure"],
    )
    _social_result = social_result or SocialPulseData(
        symbol=symbol,
        social_score=0.0,
        volume_spike_flag=False,
        dominant_platform="Fallback",
        top_keywords=[],
        sentiment_label="neutral",
        signal="HOLD",
        confidence=0.3,
        reasoning="Social intelligence unavailable — using fallback.",
        key_triggers=["Social buzz data unavailable"],
    )
    _options_result = options_result or OptionsFlowData(
        symbol=symbol,
        pcr=1.0,
        iv_rank=0.0,
        max_pain=0.0,
        gex_net=0.0,
        oi_change_velocity=0.0,
        signal="HOLD",
        confidence=0.3,
        reasoning="Options flow data unavailable — using fallback.",
        key_triggers=["F&O data ingestion failure"],
    )
    _earnings_result = earnings_result or EarningsWhisperData(
        symbol=symbol,
        whisper_score=5.0,
        surprise_probability=0.5,
        concall_tone="cautious",
        alternative_data_proxy="none",
        signal="HOLD",
        confidence=0.3,
        reasoning="Earnings whisper engine unavailable — using fallback.",
        key_triggers=["Earnings cues unavailable"],
    )

    try:
        synth_result = await synthesis.run(
            symbol,
            tech_result,
            fund_result,
            _sent_result,
            _risk_result,
            _ml_prediction,
            _macro_result,
            _reg_result,
            _social_result,
            _options_result,
            _earnings_result,
        )

        # Stage 3.5: Critic review runs when any valid agent disagrees with synthesis.
        critic_result = None
        try:
            critic_result = await critic.run(
                symbol=symbol,
                synthesis_result=synth_result,
                agent_outputs={
                    "technical": tech_result,
                    "fundamental": fund_result,
                    "sentiment": _sent_result,
                    "risk": _risk_result,
                    "ml_prediction": _ml_prediction,
                    "macro": _macro_result,
                    "synthesis": synth_result,
                },
            )
            _save_success(run_id, symbol, "critic", critic_result)
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            logger.error("✗ %s critic FAILED: %s", symbol, error_msg)
            _save_failure(run_id, symbol, "critic", error_msg)

        if critic_result is not None and critic_result.confidence_penalty > 0.0:
            synth_result.overall_confidence = round(
                max(0.0, synth_result.overall_confidence - critic_result.confidence_penalty),
                2,
            )

            if critic_result.challenges:
                challenge_note = " | ".join(critic_result.challenges[:2])
                if synth_result.conflict_notes:
                    synth_result.conflict_notes = (
                        f"{synth_result.conflict_notes}; Critic: {challenge_note}"
                    )
                else:
                    synth_result.conflict_notes = f"Critic: {challenge_note}"

            synth_result.summary = (
                f"{synth_result.final_verdict} {symbol} with "
                f"{synth_result.overall_confidence:.0%} confidence. "
                f"Technical: {tech_result.signal}, Fundamental: {fund_result.signal}, "
                f"Sentiment: {_sent_result.signal}, ML: {getattr(_ml_prediction, 'verdict', _ml_prediction.signal)}, "
                f"Risk: {_risk_result.risk_level}, Macro: {_macro_result.macro_signal}."
            )

        _save_success(run_id, symbol, "synthesis", synth_result)
        save_synthesis_result(run_id, synth_result)
        logger.info(
            "✓ %s synthesis: %s (%.0f%%) target=%+.1f%%",
            symbol,
            synth_result.final_verdict,
            synth_result.overall_confidence * 100,
            synth_result.price_target_pct,
        )
    except Exception as exc:
        error_msg = f"{type(exc).__name__}: {exc}"
        logger.error("✗ %s synthesis FAILED: %s", symbol, error_msg)
        _save_failure(run_id, symbol, "synthesis", error_msg)


# ──────────────────────────────────────────────────────────────────────
# Main entry point
# ──────────────────────────────────────────────────────────────────────
async def _run_analysis_async(run_id: str, symbols: list[str]) -> None:
    """
    Async entry point.
    """
    logger.info("▶ Analysis run %s started for symbols: %s", run_id, symbols)

    # Stage 1: Parallel Ingestion
    context_dict = await _run_data_ingestion_stage(run_id, symbols)
    symbols_with_data = list(context_dict.keys())

    if not symbols_with_data:
        _save_failure(run_id, "ALL", "eda", "Skipped - no ingestion symbols")
        update_run_status(run_id, "failed")
        return

    # Stage 2: EDA, ML, and Macro in parallel
    # Note: ML stage internally handles symbol parallelism
    ml_predictions, macro_results, _ = await asyncio.gather(
        _run_eda_and_ml_stage(run_id, symbols_with_data, context_dict),
        _run_macro_stage(run_id, symbols_with_data),
        asyncio.sleep(0), # Yield control
    )

    # Stage 3: Per-symbol analysis with concurrency control
    # Limits to 6 concurrent symbols to satisfy user speed requirements
    MAX_CONCURRENT_SYMBOLS = 6
    sem = asyncio.Semaphore(MAX_CONCURRENT_SYMBOLS)

    async def _analyze_with_sem(symbol: str):
        async with sem:
            try:
                await _run_symbol_analysis_stage(
                    run_id,
                    symbol,
                    context_dict[symbol],
                    ml_predictions.get(symbol),
                    macro_results.get(symbol),
                )
            except Exception as exc:
                logger.exception("✗ %s analysis crashed: %s", symbol, exc)
                _save_failure(run_id, symbol, "orchestrator", str(exc))

    await asyncio.gather(*[_analyze_with_sem(s) for s in symbols_with_data])

    # Final status update
    final_status = "completed" if symbols_with_data else "failed"
    update_run_status(run_id, final_status)
    logger.info("■ Analysis run %s finished: %s", run_id, final_status)


def run_analysis(run_id: str, symbols: list[str]) -> None:
    """
    Synchronous entry point called by FastAPI BackgroundTasks.
    Creates a new event loop to run the async pipeline.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_run_analysis_async(run_id, symbols))
        finally:
            loop.close()
    except Exception as exc:
        logger.error(
            "Orchestrator crashed for run %s: %s\n%s",
            run_id,
            exc,
            traceback.format_exc(),
        )
        update_run_status(run_id, "failed")
