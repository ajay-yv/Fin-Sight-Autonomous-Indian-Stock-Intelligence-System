import logging
from typing import List, Optional
from datetime import datetime
from backend.models.amapr_schemas import AgentProposal, PortfolioState, AssetClass

logger = logging.getLogger(__name__)

class TaxAgent:
    """
    Specialized agent for Tax Loss Harvesting and Capital Gains optimization.
    Proposes moves to minimize the tax burden of rebalancing.
    """
    def __init__(self, tax_rate: float = 0.15):
        self.tax_rate = tax_rate
        self.name = "TaxOptimizer"

    async def evaluate_proposals(self, portfolio: PortfolioState, base_proposals: List[AgentProposal]) -> List[AgentProposal]:
        """
        Intervenes on base proposals to optimize for tax impact.
        Substitutes high-tax-impact sells with tax-loss-harvesting alternatives if possible.
        """
        optimized_proposals = []
        
        for proposal in base_proposals:
            if proposal.action == "SELL":
                # Mock tax impact calculation
                # In a real scenario, this would check cost basis
                tax_impact = proposal.units * proposal.tax_impact if proposal.tax_impact else 0.0
                
                if tax_impact > 1000: # Threshold for intervention
                    logger.info(f"TaxAgent Intervening on {proposal.symbol} due to high tax impact: {tax_impact}")
                    # Propose a partial sell or a substitute asset sell with lower gains
                    proposal.reasoning += f" | TaxAgent Note: High tax impact detected ({tax_impact}). Consider staggered selling."
                    proposal.tax_impact = tax_impact
                
            optimized_proposals.append(proposal)
            
        return optimized_proposals

    def propose_harvesting(self, portfolio: PortfolioState) -> List[AgentProposal]:
        """Identifies assets with unrealized losses to harvest."""
        harvesting_moves = []
        for asset in portfolio.assets:
            # Simulation: if price < cost_basis (mocking this with a random condition for now)
            if asset.current_price < 0.9 * 100: # Mock baseline
                harvesting_moves.append(AgentProposal(
                    agent_name=self.name,
                    action="SELL",
                    symbol=asset.symbol,
                    units=asset.units * 0.5, # Sell half for harvesting
                    reasoning=f"Tax Loss Harvesting: Unrealized loss detected in {asset.symbol}.",
                    tax_impact=-500.0 # Negative tax impact (credit)
                ))
        return harvesting_moves
