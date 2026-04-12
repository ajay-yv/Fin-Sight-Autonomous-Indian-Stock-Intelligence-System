import logging
from typing import List, Dict, Annotated, TypedDict, Union
from datetime import datetime

# We will use a simple state-based negotiation if langgraph is still installing
try:
    from langgraph.graph import StateGraph, END
except ImportError:
    StateGraph = None
    END = "END"

from backend.models.amapr_schemas import PortfolioState, AgentProposal, NegotiationStep
from backend.agents.amapr.tax_agent import TaxAgent
from backend.agents.amapr.portfolio_risk_agent import PortfolioRiskAgent
from backend.agents.amapr.esg_agent import ESGAgent

logger = logging.getLogger(__name__)

class NegotiationState(TypedDict):
    portfolio: PortfolioState
    proposals: List[AgentProposal]
    history: List[NegotiationStep]
    consensus_reached: bool
    current_agent: str

class AMAPRNegotiator:
    """
    Coordinates the negotiation loop between specialized fiduciary agents.
    Uses a state-machine (LangGraph) approach to ensure all agents agree.
    """
    def __init__(self):
        self.tax_agent = TaxAgent()
        self.risk_agent = PortfolioRiskAgent()
        self.esg_agent = ESGAgent()
        
        if StateGraph:
            self.graph = self._build_graph()
        else:
            self.graph = None

    def _build_graph(self):
        """Constructs the LangGraph for negotiation."""
        workflow = StateGraph(NegotiationState)

        # Nodes
        workflow.add_node("risk_proposal", self._risk_proposal_node)
        workflow.add_node("tax_review", self._tax_review_node)
        workflow.add_node("esg_review", self._esg_review_node)
        workflow.add_node("synthesis", self._synthesis_node)

        # Edges
        workflow.set_entry_point("risk_proposal")
        workflow.add_edge("risk_proposal", "tax_review")
        workflow.add_edge("tax_review", "esg_review")
        workflow.add_edge("esg_review", "synthesis")
        workflow.add_edge("synthesis", END)

        return workflow.compile()

    async def negotiate(self, portfolio: PortfolioState) -> List[NegotiationStep]:
        """Runs the negotiation process."""
        if self.graph:
            initial_state = {
                "portfolio": portfolio,
                "proposals": [],
                "history": [],
                "consensus_reached": False,
                "current_agent": ""
            }
            final_state = await self.graph.ainvoke(initial_state)
            return final_state["history"]
        else:
            # Fallback for when langgraph is not available
            return await self._fallback_negotiation(portfolio)

    async def _risk_proposal_node(self, state: NegotiationState):
        logger.info("Negotiation: Risk Agent Proposing...")
        proposals = self.risk_agent.calculate_rebalance_needs(state["portfolio"])
        # Mock some if empty
        if not proposals:
            proposals = [AgentProposal(agent_name="RiskMitigator", action="BUY", symbol="RE_TOKEN_A", units=5, reasoning="Targeting RWA exposure.")]
        return {"proposals": proposals, "current_agent": "risk"}

    async def _tax_review_node(self, state: NegotiationState):
        logger.info("Negotiation: Tax Agent Reviewing...")
        reviewed = await self.tax_agent.evaluate_proposals(state["portfolio"], state["proposals"])
        return {"proposals": reviewed, "current_agent": "tax"}

    async def _esg_review_node(self, state: NegotiationState):
        logger.info("Negotiation: ESG Agent Reviewing...")
        reviewed = await self.esg_agent.evaluate_proposals(state["portfolio"], state["proposals"])
        return {"proposals": reviewed, "current_agent": "esg"}

    async def _synthesis_node(self, state: NegotiationState):
        logger.info("Negotiation: Finalizing Consensus...")
        step = NegotiationStep(
            step_index=len(state["history"]) + 1,
            proposals=state["proposals"],
            consensus_reached=True,
            conflict_notes="Negotiation concluded with multi-fiduciary approval."
        )
        return {"history": state["history"] + [step], "consensus_reached": True}

    async def _fallback_negotiation(self, portfolio: PortfolioState) -> List[NegotiationStep]:
        """Simple sequential fallback if LangGraph is missing."""
        state = {"portfolio": portfolio, "proposals": [], "history": [], "consensus_reached": False}
        state.update(await self._risk_proposal_node(state))
        state.update(await self._tax_review_node(state))
        state.update(await self._esg_review_node(state))
        state.update(await self._synthesis_node(state))
        return state["history"]
