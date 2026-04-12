"""
FinSight — FastAPI application entry-point.
Provides REST + SSE endpoints for the multi-agent stock intelligence system.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

# Load .env from project root
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_BASE_DIR, ".env"))

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, AsyncGenerator, List

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.routes.stock import router as stock_router
from api.services.market_data import NSEMarketDataService
from sqlalchemy import select
from sse_starlette.sse import EventSourceResponse

from backend.database import (
    AgentOutputRow,
    SessionLocal,
    get_recent_runs,
    get_run,
    init_db,
    save_agent_output,
    save_run,
    update_run_status,
)
from backend.models.schemas import (
    AnalysisRequest, SynthesisResult, AgentStatus, 
    PortfolioState, PortfolioAsset, RebalanceAction, AMAPRNegotiationResult,
    MLPrediction, MultiStockEDA, RunStatus
)
from backend.agents.execution.rebalancer_orchestrator import AMAPROrchestrator
from backend.execution_engine import ExecutionEngine
from backend.services.rwa_data_service import RWADataService

if TYPE_CHECKING:
    from backend.orchestrator import run_analysis  # noqa: F401


logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# Lifespan
# ──────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown lifecycle hook."""
    init_db()
    app.state.market_data_service = NSEMarketDataService()
    try:
        yield
    finally:
        await app.state.market_data_service.close()


# ──────────────────────────────────────────────────────────────────────
# App factory
# ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="FinSight — Indian Stock Intelligence",
    description="Autonomous multi-agent system for Indian equity analysis",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.amapr_endpoints import router as amapr_router
from api.ssap_endpoints import router as ssap_router
from api.darkpool_endpoints import router as darkpool_router
from api.gmss_endpoints import router as gmss_router
from api.biofeedback_endpoints import router as bio_router

app.include_router(stock_router)
app.include_router(amapr_router)
app.include_router(ssap_router)
app.include_router(darkpool_router)
app.include_router(gmss_router)
app.include_router(bio_router)


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────
def _build_run_status(run_data: dict) -> RunStatus:
    """Convert the dict returned by database.get_run() into a RunStatus."""
    return RunStatus(
        run_id=run_data["run_id"],
        symbols=run_data["symbols"],
        status=run_data["status"],
        agents=run_data.get("agents", {}),
        results=run_data.get("results", {}),
        started_at=run_data["started_at"],
        completed_at=run_data.get("completed_at"),
    )


# ──────────────────────────────────────────────────────────────────────
# AMAPR Portfolio Endpoints
# ──────────────────────────────────────────────────────────────────────

# Mock Global State for Demo
MOCK_PORTFOLIO = PortfolioState(
    portfolio_id="PF_USER_001",
    cash_balance=500000.0,
    assets=[
        PortfolioAsset(
            symbol="RELIANCE",
            asset_type="equity",
            quantity=50.0,
            avg_buy_price=2400.0,
            current_price=2950.0,
            value_in_inr=147500.0,
            tax_basis_date=datetime.utcnow() - timedelta(days=400) # LTCG
        ),
        PortfolioAsset(
            symbol="HDFCBANK",
            asset_type="equity",
            quantity=100.0,
            avg_buy_price=1650.0,
            current_price=1420.0,
            value_in_inr=142000.0,
            tax_basis_date=datetime.utcnow() - timedelta(days=90) # STCG
        ),
        PortfolioAsset(
            symbol="RWA_BLR_OFFICE_01",
            asset_type="rwa",
            quantity=10.0,
            avg_buy_price=1200.0,
            current_price=1250.45,
            value_in_inr=12504.5,
            tax_basis_date=datetime.utcnow() - timedelta(days=200)
        )
    ]
)

orchestrator_amapr = AMAPROrchestrator()
execution_engine = ExecutionEngine()

@app.get("/api/portfolio", response_model=PortfolioState)
async def get_portfolio():
    return MOCK_PORTFOLIO

@app.post("/api/portfolio/rebalance", response_model=AMAPRNegotiationResult)
async def propose_rebalance(actions: List[RebalanceAction]):
    """
    Simulates a rebalance proposal that goes through fiduciary negotiation.
    """
    result = await orchestrator_amapr.run_negotiation(MOCK_PORTFOLIO, actions)
    return result

@app.post("/api/portfolio/execute", response_model=PortfolioState)
async def execute_rebalance(actions: List[RebalanceAction]):
    global MOCK_PORTFOLIO
    MOCK_PORTFOLIO = execution_engine.apply_actions(MOCK_PORTFOLIO, actions)
    return MOCK_PORTFOLIO


@app.get("/api/rwa/list")
async def list_rwa_assets():
    """Return all tokenized RWA assets available on the platform."""
    rwa_service = RWADataService()
    assets = rwa_service.list_all_rwas()
    return [a.model_dump() for a in assets]


@app.get("/api/rwa/{asset_id}")
async def get_rwa_asset(asset_id: str):
    """Get details of a specific tokenized RWA asset."""
    rwa_service = RWADataService()
    asset = rwa_service.get_asset_details(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"RWA asset '{asset_id}' not found")
    return asset.model_dump()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


def _trigger_orchestrator(run_id: str, symbols: list[str]) -> None:
    """
    Import orchestrator at call-time to avoid circular import issues,
    then kick off analysis synchronously (called inside a BackgroundTask).
    """
    try:
        from backend.orchestrator import run_analysis  # lazy import

        run_analysis(run_id=run_id, symbols=symbols)
    except Exception as exc:
        logger.exception("Orchestrator task crashed for run %s", run_id)
        try:
            save_agent_output(
                run_id=run_id,
                symbol="ALL",
                agent_name="orchestrator",
                status="failed",
                signal=None,
                confidence=None,
                reasoning=f"Orchestrator bootstrap failed: {type(exc).__name__}: {exc}",
                data_dict=None,
            )
        except Exception:
            logger.exception("Failed to persist orchestrator failure for run %s", run_id)
        update_run_status(run_id, "failed")


def _get_agent_output_row(
    run_id: str,
    agent_name: str,
    symbol: str | None = None,
) -> AgentOutputRow | None:
    """Fetch latest agent_output row for run + agent (+ optional symbol)."""
    with SessionLocal() as session:
        stmt = select(AgentOutputRow).where(
            AgentOutputRow.run_id == run_id,
            AgentOutputRow.agent_name == agent_name,
        )
        if symbol is not None:
            stmt = stmt.where(AgentOutputRow.symbol == symbol)
        stmt = stmt.order_by(AgentOutputRow.id.desc())
        return session.scalar(stmt)


# ──────────────────────────────────────────────────────────────────────
# POST /analyze
# ──────────────────────────────────────────────────────────────────────
@app.post("/analyze")
async def analyze(request: AnalysisRequest, bg: BackgroundTasks) -> JSONResponse:
    """Accept an analysis request, persist it, and start the pipeline."""
    save_run(request.run_id, request.symbols)
    bg.add_task(_trigger_orchestrator, run_id=request.run_id, symbols=list(request.symbols))
    return JSONResponse(
        status_code=202,
        content={
            "run_id": request.run_id,
            "status": "started",
            "message": (
                f"Analysis started for {', '.join(request.symbols)}. "
                f"Track progress at /status/{request.run_id}"
            ),
        },
    )


# ──────────────────────────────────────────────────────────────────────
# GET /status/{run_id}
# ──────────────────────────────────────────────────────────────────────
@app.get("/status/{run_id}")
async def status(run_id: str) -> RunStatus:
    """Return the full RunStatus for a given run."""
    run_data = get_run(run_id)
    if run_data is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    return _build_run_status(run_data)


# ──────────────────────────────────────────────────────────────────────
# GET /stream/{run_id}  (SSE)
# ──────────────────────────────────────────────────────────────────────
@app.get("/stream/{run_id}")
async def stream(run_id: str) -> EventSourceResponse:
    """
    Server-Sent Events stream that polls the DB every 1.5 s and pushes
    agent-status updates as JSON.  Closes when the run completes or fails.
    """
    # Validate the run exists before opening the stream
    if get_run(run_id) is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    async def event_generator() -> AsyncGenerator[dict, None]:
        previous_snapshot: str = ""
        while True:
            run_data = get_run(run_id)
            if run_data is None:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "run_not_found"}),
                }
                break

            run_status = _build_run_status(run_data)
            current_snapshot = run_status.model_dump_json()

            # Only push when something changed
            if current_snapshot != previous_snapshot:
                yield {
                    "event": "status",
                    "data": current_snapshot,
                }
                previous_snapshot = current_snapshot

            if run_status.status in ("completed", "failed"):
                yield {
                    "event": "done",
                    "data": json.dumps({"status": run_status.status}),
                }
                break

            await asyncio.sleep(1.5)

    return EventSourceResponse(event_generator())


# ──────────────────────────────────────────────────────────────────────
# GET /runs
# ──────────────────────────────────────────────────────────────────────
@app.get("/runs")
async def runs() -> list[dict]:
    """Return the last 10 runs with their status and symbols."""
    return get_recent_runs(limit=10)


# ──────────────────────────────────────────────────────────────────────
# GET /report/{run_id}/{symbol}
# ──────────────────────────────────────────────────────────────────────
@app.get("/report/{run_id}/{symbol}")
async def report(run_id: str, symbol: str) -> JSONResponse:
    """Return the full detailed_report text for a specific symbol."""
    run_data = get_run(run_id)
    if run_data is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    symbol_upper = symbol.strip().upper()
    results: dict = run_data.get("results", {})

    if symbol_upper not in results:
        raise HTTPException(
            status_code=404,
            detail=f"No synthesis result for symbol '{symbol_upper}' in run '{run_id}'",
        )

    synthesis = results[symbol_upper]
    return JSONResponse(
        content={
            "run_id": run_id,
            "symbol": symbol_upper,
            "verdict": synthesis.final_verdict,
            "confidence": synthesis.overall_confidence,
            "summary": synthesis.summary,
            "detailed_report": synthesis.detailed_report,
            "logic_map": synthesis.logic_map,
            "generated_at": synthesis.generated_at.isoformat(),
        }
    )


# ──────────────────────────────────────────────────────────────────────
# GET /eda/{run_id}
# ──────────────────────────────────────────────────────────────────────
@app.get("/eda/{run_id}")
async def get_eda(run_id: str) -> MultiStockEDA:
    """Return run-level MultiStockEDA for a completed run."""
    run_data = get_run(run_id)
    if run_data is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    if run_data["status"] != "completed":
        raise HTTPException(status_code=409, detail=f"Run '{run_id}' is not completed yet")

    row = _get_agent_output_row(run_id=run_id, agent_name="eda")
    if row is None or row.data_json is None:
        raise HTTPException(
            status_code=404,
            detail=f"No EDA output found for run '{run_id}'",
        )
    if row.status != "completed":
        raise HTTPException(
            status_code=409,
            detail=f"EDA output for run '{run_id}' is not completed",
        )

    try:
        return MultiStockEDA.model_validate(json.loads(row.data_json))
    except Exception as exc:
        logger.exception("Failed to parse EDA output for run %s: %s", run_id, exc)
        raise HTTPException(
            status_code=500,
            detail="Stored EDA result is invalid",
        ) from exc


# ──────────────────────────────────────────────────────────────────────
# GET /ml/{run_id}/{symbol}
# ──────────────────────────────────────────────────────────────────────
@app.get("/ml/{run_id}/{symbol}")
async def get_ml_prediction(run_id: str, symbol: str) -> MLPrediction:
    """Return ML prediction output for a specific symbol in a completed run."""
    run_data = get_run(run_id)
    if run_data is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    if run_data["status"] != "completed":
        raise HTTPException(status_code=409, detail=f"Run '{run_id}' is not completed yet")

    symbol_upper = symbol.strip().upper()
    row = _get_agent_output_row(
        run_id=run_id,
        agent_name="ml_prediction",
        symbol=symbol_upper,
    )
    if row is None or row.data_json is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No ML prediction found for symbol '{symbol_upper}' "
                f"in run '{run_id}'"
            ),
        )
    if row.status != "completed":
        raise HTTPException(
            status_code=409,
            detail=(
                f"ML prediction for symbol '{symbol_upper}' "
                f"in run '{run_id}' is not completed"
            ),
        )

    try:
        return MLPrediction.model_validate(json.loads(row.data_json))
    except Exception as exc:
        logger.exception(
            "Failed to parse ML output for run %s symbol %s: %s",
            run_id,
            symbol_upper,
            exc,
        )
        raise HTTPException(
            status_code=500,
            detail="Stored ML prediction is invalid",
        ) from exc


# ──────────────────────────────────────────────────────────────────────
# GET /run/{run_id}/stock/{symbol}/ohlcv
# ──────────────────────────────────────────────────────────────────────
@app.get("/api/run/{run_id}/stock/{symbol}/ohlcv")
async def get_run_ohlcv(run_id: str, symbol: str) -> dict[str, Any]:
    """Return stored OHLCV data for a specific symbol in a run.
    Falls back to a live yfinance fetch when the DB row is missing or failed.
    """
    symbol_upper = symbol.strip().upper()
    row = _get_agent_output_row(run_id=run_id, agent_name="data_ingestion", symbol=symbol_upper)

    # ── Try to build candles from stored data first ──────────────────
    if row is not None and row.data_json is not None:
        try:
            data = json.loads(row.data_json)
            dates = data.get("dates", [])
            opens = data.get("opens", [])
            highs = data.get("highs", [])
            lows = data.get("lows", [])
            closes = data.get("closes", [])
            volumes = data.get("volumes", [])

            candles = [
                {
                    "time": dates[i],
                    "open": opens[i],
                    "high": highs[i],
                    "low": lows[i],
                    "close": closes[i],
                    "volume": volumes[i],
                }
                for i in range(len(dates))
            ]
            if candles:
                return {"symbol": symbol_upper, "candles": candles}
        except Exception as exc:
            logger.warning(
                "Failed to parse stored OHLCV for run %s symbol %s, will attempt live fetch: %s",
                run_id, symbol_upper, exc,
            )

    # ── Fallback: live fetch via yfinance ────────────────────────────
    logger.info(
        "OHLCV not in DB for run %s symbol %s — fetching live via yfinance",
        run_id, symbol_upper,
    )
    try:
        from backend.agents import data_ingestion as _di
        ohlcv = await _di.run(symbol_upper)
        candles = [
            {
                "time": ohlcv.dates[i],
                "open": ohlcv.opens[i],
                "high": ohlcv.highs[i],
                "low": ohlcv.lows[i],
                "close": ohlcv.closes[i],
                "volume": ohlcv.volumes[i],
            }
            for i in range(len(ohlcv.dates))
        ]
        # Persist the freshly fetched data so next request hits the DB
        from backend.database import save_agent_output as _sao
        _sao(
            run_id=run_id,
            symbol=symbol_upper,
            agent_name="data_ingestion",
            status="completed",
            signal=None,
            confidence=None,
            reasoning=f"Live fallback fetch: {len(ohlcv.dates)} days",
            data_dict=ohlcv.model_dump(mode="json"),
        )
        return {"symbol": symbol_upper, "candles": candles}
    except Exception as exc:
        logger.exception(
            "Live OHLCV fallback also failed for run %s symbol %s: %s",
            run_id, symbol_upper, exc,
        )
        raise HTTPException(
            status_code=404,
            detail=f"No OHLCV data available for '{symbol_upper}'. Live fetch also failed: {exc}",
        ) from exc


# ──────────────────────────────────────────────────────────────────────
# GET /health
# ──────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health() -> dict:
    """Simple liveness probe."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
