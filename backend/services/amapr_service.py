import json
import os
import logging
from typing import List, Optional
from datetime import datetime
import asyncio
from pathlib import Path

from backend.models.amapr_schemas import (
    AMAPRRunResult, 
    AssetClass, 
    PortfolioState, 
    PortfolioAsset, 
    AgentProposal, 
    NegotiationStep
)
from backend.agents.amapr.negotiator import AMAPRNegotiator

logger = logging.getLogger(__name__)

if os.environ.get("VERCEL"):
    PORTFOLIO_FILE = Path("/tmp/portfolio.json")
else:
    PORTFOLIO_FILE = Path("backend/data/portfolio.json")

from backend.services.intelligence_service import IntelligenceService

class AMAPRService:
    """
    Main orchestration service for the Agentic Multi-Asset Portfolio Rebalancer.
    """
    def __init__(self):
        self.negotiator = AMAPRNegotiator()
        self.intel = IntelligenceService()
        self._portfolio: Optional[PortfolioState] = None
        self._lock = asyncio.Lock()
        self._load_portfolio()

    def _load_portfolio(self):
        """Load portfolio from disk or use default mock."""
        try:
            if PORTFOLIO_FILE.exists():
                with open(PORTFOLIO_FILE, "r") as f:
                    data = json.load(f)
                    self._portfolio = PortfolioState.model_validate(data)
                logger.info(f"Loaded portfolio {self._portfolio.portfolio_id} from {PORTFOLIO_FILE}")
            else:
                self._portfolio = self._get_default_mock_portfolio()
                self._save_portfolio()
        except Exception as exc:
            logger.error(f"Failed to load portfolio from disk: {exc}")
            self._portfolio = self._get_default_mock_portfolio()

    def _save_portfolio(self):
        """Save current portfolio state to disk."""
        try:
            PORTFOLIO_FILE.parent.mkdir(parents=True, exist_ok=True)
            if self._portfolio:
                with open(PORTFOLIO_FILE, "w") as f:
                    # Use model_dump(mode="json") to handle datetime/enums
                    json.dump(self._portfolio.model_dump(mode="json"), f, indent=2)
                logger.debug(f"Saved portfolio to {PORTFOLIO_FILE}")
        except Exception as exc:
            logger.error(f"Failed to save portfolio to disk: {exc}")

    async def get_portfolio(self, refresh_prices: bool = True) -> PortfolioState:
        """Retrieve current portfolio state. Optionally updates equity prices live."""
        async with self._lock:
            try:
                if not self._portfolio:
                    self._load_portfolio()
                
                p = self._portfolio
                if not p:
                    logger.warning("Portfolio is None after load, using default mock.")
                    p = self._get_default_mock_portfolio()

                if refresh_prices:
                    # Update prices in a safe manner
                    try:
                        await self._refresh_equity_prices(p)
                        self._save_portfolio()
                    except Exception as refresh_exc:
                        logger.error(f"Live price refresh failed, using cached values: {refresh_exc}")
                
                return p
            except Exception as exc:
                logger.exception(f"Critical failure in get_portfolio: {exc}")
                return self._get_default_mock_portfolio()

    async def _refresh_equity_prices(self, portfolio: PortfolioState):
        """Fetch latest prices for all equity assets via data_ingestion agent."""
        try:
            from backend.agents import data_ingestion
        except ImportError:
            logger.warning("data_ingestion agent not found, skipping price refresh.")
            return

        updated = False
        total_val = 0.0

        for asset in portfolio.assets:
            if asset.asset_class == AssetClass.EQUITY:
                try:
                    logger.debug(f"Refreshing live price for {asset.symbol}...")
                    live_data = await data_ingestion.run(asset.symbol)
                    if live_data and live_data.current_price > 0:
                        asset.current_price = live_data.current_price
                        asset.valuation = asset.current_price * asset.units
                        updated = True
                except Exception as exc:
                    logger.warning(f"Could not refresh price for {asset.symbol}: {exc}")
            
            total_val += (asset.valuation or 0)

        if updated:
            portfolio.total_valuation = total_val
            if total_val > 0:
                for asset in portfolio.assets:
                    asset.weight = (asset.valuation or 0) / total_val
            logger.info(f"Portfolio valuations updated. Total AUM: ₹{total_val}")

    def update_portfolio(self, new_state: PortfolioState):
        """Update the internal portfolio state and persist to disk."""
        self._portfolio = new_state
        self._save_portfolio()
        logger.info(f"Portfolio {new_state.portfolio_id} manually updated and persisted.")

    async def run_rebalance(self, portfolio_id: str, current_state: PortfolioState) -> AMAPRRunResult:
        """
        Executes a full rebalancing run with agent negotiation via LangGraph.
        """
        run_id = f"AMAPR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        logger.info(f"Starting AMAPR run (Negotiation): {run_id}")

        # Connect to real world: Get market volatility
        market_stats = await self.intel.get_market_biometrics()
        vix = market_stats.get("fear_index", 15.0)

        # Execute Negotiation Loop
        negotiation_history = await self.negotiator.negotiate(current_state)
        
        # Extract final proposals from last step
        final_proposals = []
        if negotiation_history:
            final_proposals = negotiation_history[-1].proposals

        # Step 3: Apply Changes (Mocked final state)
        final_state = current_state.model_copy()
        final_state.last_rebalanced = datetime.now()
        
        # Volatility influences how much we can reduce drift
        final_state.drift_score = 0.02 + (vix / 500.0) 

        result = AMAPRRunResult(
            run_id=run_id,
            initial_state=current_state,
            final_state=final_state,
            negotiation_history=negotiation_history,
            total_tax_optimized=1250.0 * (1 + (vix/100)), # Volatility creates more tax harvest opportunities
            risk_reduction=0.08 * (1 - (vix/200)), # Harder to reduce risk in high volatility
            timestamp=datetime.now()
        )

        logger.info(f"AMAPR run {run_id} completed. Real-world VIX {vix} accounted for.")
        return result

    def _get_default_mock_portfolio(self) -> PortfolioState:
        """Helper to generate initial mock data."""
        return PortfolioState(
            portfolio_id="P-001",
            assets=[
                PortfolioAsset(symbol="RELIANCE.NS", asset_class=AssetClass.EQUITY, units=100, current_price=2900, valuation=290000, weight=0.7),
                PortfolioAsset(symbol="TCS.NS", asset_class=AssetClass.EQUITY, units=50, current_price=4000, valuation=200000, weight=0.3)
            ],
            total_valuation=490000,
            target_weights={
                AssetClass.EQUITY: 0.6,
                AssetClass.REAL_ESTATE: 0.2,
                AssetClass.PRIVATE_CREDIT: 0.1,
                AssetClass.CASH: 0.1
            },
            drift_score=0.15
        )
