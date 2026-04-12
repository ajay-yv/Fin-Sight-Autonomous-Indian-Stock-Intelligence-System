import uuid
import logging
from typing import List, Dict
from datetime import datetime
from backend.models.schemas import (
    PortfolioState, RebalanceAction, AMAPRNegotiationResult
)
from backend.agents.execution.fiduciary_agents import (
    TaxAgent, ESGAgent, RiskFiduciaryAgent
)

logger = logging.getLogger(__name__)

class AMAPROrchestrator:
    def __init__(self):
        self.agents = [
            TaxAgent(),
            ESGAgent(),
            RiskFiduciaryAgent()
        ]

    async def run_negotiation(
        self, 
        current_state: PortfolioState, 
        proposed_actions: List[RebalanceAction]
    ) -> AMAPRNegotiationResult:
        """
        Runs the fiduciary negotiation loop.
        Agents can approve, reject, or suggest penalties.
        """
        run_id = str(uuid.uuid4())
        final_actions = []
        agent_consensus = {agent.name: "pending" for agent in self.agents}
        
        total_tax_penalty = 0.0
        total_esg_score = 1.0 # Start perfect
        
        for action in proposed_actions:
            action_approved = True
            action_reasons = []
            
            # Negotiation Loop for each action
            for agent in self.agents:
                approved, reason, penalty = await agent.evaluate_action(action, current_state)
                
                if not approved:
                    action_approved = False
                    agent_consensus[agent.name] = "REJECTED"
                else:
                    if agent_consensus[agent.name] != "REJECTED":
                        agent_consensus[agent.name] = "APPROVED"
                
                action_reasons.append(f"{agent.name}: {reason}")
                
                if agent.name == "TaxOptimizer":
                    total_tax_penalty += penalty
                if agent.name == "ESGCompliance":
                    total_esg_score -= penalty

            if action_approved:
                action.reason = " | ".join(action_reasons)
                action.fiduciary_approval = [a.name for a in self.agents]
                final_actions.append(action)
            else:
                logger.warning(f"Action for {action.symbol} rejected by fiduciary board: {action_reasons}")

        # Final synthesis of the negotiation
        verdict = "STABLE"
        if not final_actions:
            verdict = "BLOCKED"
        elif len(final_actions) < len(proposed_actions):
            verdict = "PARTIAL_CONSENSUS"
        else:
            verdict = "FULLY_APPROVED"

        return AMAPRNegotiationResult(
            run_id=run_id,
            original_state=current_state,
            proposed_actions=final_actions,
            final_verdict=verdict,
            agent_consensus=agent_consensus,
            tax_optimization_saved=total_tax_penalty * 10000, # Mock saving scaling
            esg_compliance_score=max(0, total_esg_score)
        )
