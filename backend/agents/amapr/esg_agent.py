import logging
from typing import List, Dict
from backend.models.amapr_schemas import AgentProposal, PortfolioState, AssetClass

logger = logging.getLogger(__name__)

class ESGAgent:
    """
    Ensures portfolio stays within Environmental, Social, and Governance thresholds.
    Can veto assets or propose replacements with higher ESG scores.
    """
    def __init__(self, min_esg_score: float = 70.0):
        self.min_esg_score = min_esg_score
        self.name = "ESGGuardian"

    async def evaluate_proposals(self, portfolio: PortfolioState, base_proposals: List[AgentProposal]) -> List[AgentProposal]:
        """
        Vetoes proposals that violate ESG compliance.
        """
        final_proposals = []
        for prop in base_proposals:
            # Mock ESG lookup
            esg_score = self._get_mock_esg_score(prop.symbol)
            
            if esg_score < self.min_esg_score:
                logger.warning(f"ESGAgent: VETO on {prop.symbol} due to low ESG score: {esg_score}")
                prop.esg_impact = -1.0 # High negative impact
                prop.action = "HOLD" # Vetoed BUY/SELL
                prop.reasoning += f" | ESGAgent Veto: Asset ESG score ({esg_score}) below threshold ({self.min_esg_score})."
            else:
                prop.esg_impact = 1.0 # Positive impact
                
            final_proposals.append(prop)
            
        return final_proposals

    def _get_mock_esg_score(self, symbol: str) -> float:
        """Returns a mock ESG score for a symbol."""
        # Simulations
        if "RE" in symbol: # Real estate token might have higher ESG focus
            return 85.0
        return 75.0 # Baseline
