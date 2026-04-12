import logging
from typing import List, Dict
from backend.models.gmss_schemas import SimulationReport, PropagationDelta, MacroShock
from backend.services.gmss.abm_engine import ABMEngine
from backend.services.gmss.scenario_engine import ScenarioEngine

logger = logging.getLogger(__name__)

class GMSSService:
    """
    Orchestrates the Generative Macro-Scenario Simulator (GMSS).
    Coordinates Scenario generation and Agent-Based Modeling propagation.
    """
    def __init__(self):
        self.scenario_engine = ScenarioEngine()
        self.abm_engine = ABMEngine()
        # In-memory store for prototype
        self.simulations: Dict[str, SimulationReport] = {}

    async def start_simulation(self, scenario_key: str) -> SimulationReport:
        """
        Initializes and runs a full macro-scenario simulation.
        """
        logger.info(f"Starting GMSS Simulation: {scenario_key}")
        
        # 1. Generate Shock
        shock = await self.scenario_engine.generate_shock(scenario_key)
        
        # 2. Run ABM Propagation
        all_steps_deltas = []
        # Simulate over the duration of the shock
        for month in range(shock.duration_months):
            step_deltas = self.abm_engine.run_step(month, shock.initial_magnitude, shock.target_sectors)
            all_steps_deltas.extend(step_deltas)

        # 3. Compile Report
        report = SimulationReport(
            simulation_id=f"SIM-{shock.shock_id}",
            shock=shock,
            propagation_steps=all_steps_deltas,
            affected_sectors=shock.target_sectors,
            max_supply_chain_stress=max([d.supply_chain_stress for d in all_steps_deltas]),
            recovery_estimated_months=shock.duration_months * 2,
            narrative_summary=f"The {scenario_key} shock targets {', '.join(shock.target_sectors)}. "
                              f"Initial stress is high, with supply chain recovery expected over {shock.duration_months * 2} months."
        )
        
        self.simulations[report.simulation_id] = report
        return report

    def get_simulation_report(self, sim_id: str) -> SimulationReport:
        return self.simulations.get(sim_id)
