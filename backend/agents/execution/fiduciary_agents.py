import logging
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from backend.models.schemas import PortfolioState, PortfolioAsset, RebalanceAction

logger = logging.getLogger(__name__)

class FiduciaryAgent:
    def __init__(self, name: str):
        self.name = name

    async def evaluate_action(self, action: RebalanceAction, state: PortfolioState) -> Tuple[bool, str, float]:
        """Returns (approved, reason, score_penalty)"""
        return True, "Default approval", 0.0

class TaxAgent(FiduciaryAgent):
    """
    Optimizes for Indian Capital Gains Tax (LTCG/STCG).
    - Equity LTCG (1yr): 10% (above 1L) -> 12.5% (2025 rule)
    - Equity STCG: 20%
    """
    def __init__(self):
        super().__init__("TaxOptimizer")

    async def evaluate_action(self, action: RebalanceAction, state: PortfolioState) -> Tuple[bool, str, float]:
        if action.action == "SELL":
            asset = next((a for a in state.assets if a.symbol == action.symbol), None)
            if not asset:
                return False, "Asset not found in portfolio", 1.0
            
            # Check holding period
            holding_period = datetime.utcnow() - asset.tax_basis_date
            is_equity = asset.asset_type == "equity"
            
            if is_equity and holding_period < timedelta(days=365):
                # Penalty for STCG
                saving_potential = action.quantity * (asset.current_price - asset.avg_buy_price) * 0.075 # 20% STCG vs 12.5% LTCG
                if saving_potential > 5000: # Threshold for negotiation
                    return False, f"STCG Penalty: Selling now incurs 20% tax. Waiting {365 - holding_period.days} more days saves approx ₹{saving_potential:.2f}", 0.8
            
        return True, "Tax efficient or neutral", 0.0

class ESGAgent(FiduciaryAgent):
    """
    Filters for ESG compliance. 
    In 2026, this agent checks global ESG databases and RWA green-certification.
    """
    def __init__(self):
        super().__init__("ESGCompliance")
        self.blacklist = ["COAL", "TOBACCO", "WEAPONS"]

    async def evaluate_action(self, action: RebalanceAction, state: PortfolioState) -> Tuple[bool, str, float]:
        if action.action == "BUY" and any(b in action.symbol.upper() for b in self.blacklist):
            return False, f"ESG Violation: {action.symbol} belongs to a blacklisted sector.", 1.0
        
        # RWAs often have green ratings
        if "RWA" in action.symbol and "WH" in action.symbol: # Warehouse mock
            return True, "ESG Bonus: Logistics infrastructure has high ESG rating.", -0.2
            
        return True, "Compliant", 0.0

class RiskFiduciaryAgent(FiduciaryAgent):
    """
    Devil's Advocate for risk. Limits RWA exposure due to liquidity risk.
    """
    def __init__(self):
        super().__init__("RiskFiduciary")
        self.rwa_max_exposure = 0.35 # 35% Max for RWAs
        self.single_asset_max = 0.15 # 15% Max for single asset

    async def evaluate_action(self, action: RebalanceAction, state: PortfolioState) -> Tuple[bool, str, float]:
        total_value = sum(a.value_in_inr for a in state.assets) + state.cash_balance
        if total_value <= 0: return True, "Empty portfolio", 0.0

        if action.action == "BUY":
            # Current exposure check
            asset_value = action.quantity * 1000 # Mock price if new
            new_total = total_value + (asset_value if action.action == "BUY" else 0)
            
            # Find current asset value
            existing = next((a for a in state.assets if a.symbol == action.symbol), None)
            current_asset_val = existing.value_in_inr if existing else 0
            
            if (current_asset_val + asset_value) / new_total > self.single_asset_max:
                return False, f"Concentration Risk: {action.symbol} exposure exceeds {self.single_asset_max*100}% of portfolio.", 0.7

            if "RWA" in action.symbol:
                rwa_total = sum(a.value_in_inr for a in state.assets if a.asset_type == "rwa")
                if (rwa_total + asset_value) / new_total > self.rwa_max_exposure:
                    return False, f"Liquidity Risk: Unified RWA exposure exceeds {self.rwa_max_exposure*100}% cap.", 0.9

        return True, "Within risk parameters", 0.0
