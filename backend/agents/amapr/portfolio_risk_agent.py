import logging
import numpy as np
from typing import List, Dict
from backend.models.amapr_schemas import AgentProposal, PortfolioState, AssetClass

logger = logging.getLogger(__name__)

class PortfolioRiskAgent:
    """
    Manages portfolio-level risk, looking at correlations between 
    traditional equities and tokenized RWAs.
    """
    def __init__(self, target_volatility: float = 0.12):
        self.target_volatility = target_volatility
        self.name = "RiskMitigator"

    async def evaluate_proposals(self, portfolio: PortfolioState, base_proposals: List[AgentProposal]) -> List[AgentProposal]:
        """
        Adjusts proposals to ensure portfolio risk remains within bounds.
        May reduce position sizes if concentration risk is too high.
        """
        # Calculate current concentration
        asset_weights = {asset.symbol: asset.weight for asset in portfolio.assets}
        
        modified_proposals = []
        for prop in base_proposals:
            new_weight = asset_weights.get(prop.symbol, 0)
            if prop.action == "BUY":
                # Mock calculation of weight after buy
                # If we're buying something already > 5% of portfolio, add a warning
                if new_weight > 0.05:
                    logger.warning(f"RiskAgent: Concentration risk detected in {prop.symbol} (Weight: {new_weight:.1%})")
                    prop.units *= 0.8 # Reduce buy size by 20%
                    prop.reasoning += f" | RiskAgent Note: Reducing size to mitigate concentration risk."
            
            modified_proposals.append(prop)
            
        return modified_proposals

    def calculate_rebalance_needs(self, portfolio: PortfolioState) -> List[AgentProposal]:
        """Identifies assets that have drifted significantly from target allocations."""
        proposals = []
        # Group current weights by Asset Class
        current_alloc = {}
        for asset in portfolio.assets:
            current_alloc[asset.asset_class] = current_alloc.get(asset.asset_class, 0) + asset.weight
            
        for asset_class, target in portfolio.target_weights.items():
            current = current_alloc.get(asset_class, 0)
            drift = current - target
            
            if abs(drift) > 0.05: # 5% drift threshold
                logger.info(f"RiskAgent: Large drift detected in {asset_class}: {drift:+.1%}")
                # Propose a general rebalance move (specific assets would be picked by a lower-level agent or strategy)
                # For simplicity, we just flag the need here.
        
        return proposals
