from fastapi import APIRouter, HTTPException
from backend.models.gmss_schemas import SimulationReport
from backend.services.gmss.gmss_service import GMSSService

router = APIRouter(prefix="/api/gmss", tags=["Macro Simulator"])
gmss_service = GMSSService()

@router.post("/simulate/{scenario_key}", response_model=SimulationReport)
async def run_macro_simulation(scenario_key: str):
    """
    Trigger a macro-scenario simulation for a specific black-swan event.
    """
    try:
        return await gmss_service.start_simulation(scenario_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/report/{sim_id}", response_model=SimulationReport)
async def get_simulation_report(sim_id: str):
    """
    Retrieve the full propagation and impact report for a previous simulation.
    """
    report = gmss_service.get_simulation_report(sim_id)
    if not report:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return report
