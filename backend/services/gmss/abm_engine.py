import random
import logging
from typing import List, Dict
from backend.models.gmss_schemas import AgentState, PropagationDelta

logger = logging.getLogger(__name__)

class ABMEngine:
    """
    Agent-Based Modeling (ABM) Engine for Macro-Scenario Simulation.
    Simulates thousands of autonomous agents (Households, Firms) to observe 
    emergent macro-economic behaviors under stress.
    """
    def __init__(self):
        self.sectors = ["ENERGY", "LOGISTICS", "RETAIL", "FINANCE", "TECH"]
        self.agents: List[AgentState] = []
        self._initialize_population()

    def _initialize_population(self):
        """Creates a representative sample of agents across sectors."""
        for i in range(100): # Representative sample for prototype
            sector = random.choice(self.sectors)
            self.agents.append(AgentState(
                agent_id=f"AG_{sector}_{i}",
                sector=sector,
                sentiment=random.uniform(0.6, 0.9),
                liquidity=random.uniform(1000, 10000),
                resilience=random.uniform(0.5, 0.9)
            ))

    def run_step(self, step: int, shock_intensity: float, affected_sectors: List[str]) -> List[PropagationDelta]:
        """
        Executes one step (month) of the simulation.
        Shocks propagate from target sectors to the rest of the economy.
        """
        deltas = []
        
        for sector in self.sectors:
            sector_agents = [a for a in self.agents if a.sector == sector]
            
            # Base disruption
            is_directly_affected = sector in affected_sectors
            disruption = (shock_intensity if is_directly_affected else shock_intensity * 0.4) / (1 + step)
            
            # Update agents
            avg_sentiment = 0
            for agent in sector_agents:
                # Stochastic reaction based on resilience
                reaction = disruption * (1.2 - agent.resilience)
                agent.sentiment = max(0.1, agent.sentiment - reaction)
                avg_sentiment += agent.sentiment
            
            avg_sentiment /= len(sector_agents)
            
            # Calculate Propagation Delta
            deltas.append(PropagationDelta(
                step=step,
                target_sector=sector,
                inflation_delta=disruption * 5.0, # 5% inflation multiplier for shock
                supply_chain_stress=min(1.0, disruption * 2.0),
                gdp_impact=-(disruption * 10.0),
                market_volatility=disruption * 3.0
            ))
            
        return deltas
