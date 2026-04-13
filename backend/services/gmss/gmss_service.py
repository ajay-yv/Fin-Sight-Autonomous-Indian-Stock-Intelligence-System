import logging
from typing import List, Dict
from backend.models.gmss_schemas import SimulationReport, PropagationDelta, MacroShock
from backend.services.gmss.abm_engine import ABMEngine
from backend.services.gmss.scenario_engine import ScenarioEngine

logger = logging.getLogger(__name__)

from backend.services.intelligence_service import IntelligenceService

class GMSSService:
    """
    Orchestrates the Generative Macro-Scenario Simulator (GMSS).
    """
    def __init__(self):
        self.scenario_engine = ScenarioEngine()
        self.abm_engine = ABMEngine()
        self.intel = IntelligenceService()
        self.simulations: Dict[str, SimulationReport] = {}

    async def start_simulation(self, scenario_key: str) -> SimulationReport:
        """
        Initializes and runs a full macro-scenario simulation.
        """
        logger.info(f"Starting GMSS Simulation: {scenario_key}")
        
        # Connect to real world: Get current macro baseline
        macro_baseline = await self.intel.get_macro_indicators()
        vix = macro_baseline.get("india_vix", 15.0)
        
        # 1. Generate Shock (with VIX-based volatility multiplier)
        shock = await self.scenario_engine.generate_shock(scenario_key)
        
        # Influence shock magnitude by real world volatility
        vol_multiplier = 1.0 + (vix / 50.0) # VIX of 25 adds 50% intensity
        logger.info(f"Real-world VIX {vix} applying x{vol_multiplier:.2f} shock multiplier")
        
        # 2. Run ABM Propagation
        all_steps_deltas = []
        # Simulate over the duration of the shock
        for month in range(shock.duration_months):
            # Applying vol_multiplier to reflect real-world stress
            effective_magnitude = shock.initial_magnitude * vol_multiplier
            step_deltas = self.abm_engine.run_step(month, effective_magnitude, shock.target_sectors)
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
