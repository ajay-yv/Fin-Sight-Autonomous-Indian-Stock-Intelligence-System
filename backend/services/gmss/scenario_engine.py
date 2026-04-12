import logging
import uuid
from datetime import datetime
from typing import List
from backend.models.gmss_schemas import MacroShock

logger = logging.getLogger(__name__)

class ScenarioEngine:
    """
    Generative Scenario Engine using Llama 3.1 logic (Simulated).
    Translates abstract "Black Swan" event descriptions into quantitative shock parameters.
    """
    def __init__(self):
        self.scenarios = {
            "SUEZ_BLOCKAGE": {
                "description": "Critical maritime route blockage in Suez Canal due to ground vessel.",
                "magnitude": 0.85,
                "sectors": ["LOGISTICS", "ENERGY", "RETAIL"],
                "months": 4
            },
            "CLIMATE_HEATWAVE": {
                "description": "Record-breaking heatwave across SE Asia disrupting electronics manufacturing.",
                "magnitude": 0.65,
                "sectors": ["TECH", "ENERGY"],
                "months": 6
            },
            "BANKING_LIQUIDITY": {
                "description": "Sudden liquidity crunch in mid-tier regional banks due to treasury de-valuation.",
                "magnitude": 0.95,
                "sectors": ["FINANCE", "TECH"],
                "months": 12
            }
        }

    async def generate_shock(self, scenario_key: str) -> MacroShock:
        """
        Retrieves or generates a macro shock based on the scenario type.
        """
        logger.info(f"Generating synthetic shock for: {scenario_key}")
        
        config = self.scenarios.get(scenario_key.upper(), {
            "description": f"Custom {scenario_key} geopolitical event detected.",
            "magnitude": 0.5,
            "sectors": ["FINANCE"],
            "months": 3
        })

        return MacroShock(
            shock_id=f"SHOCK-{uuid.uuid4().hex[:6]}",
            event_type="GEOPOLITICAL", # Default to Geo for sample
            description=config["description"],
            initial_magnitude=config["magnitude"],
            target_sectors=config["sectors"],
            duration_months=config["months"],
            started_at=datetime.now()
        )
