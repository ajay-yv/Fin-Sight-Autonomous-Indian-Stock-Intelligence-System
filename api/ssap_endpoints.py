from fastapi import APIRouter, HTTPException
from backend.models.ssap_schemas import SSAPVerdict
from backend.services.ssap_service import SSAPService

router = APIRouter(prefix="/api/ssap", tags=["SSAP"])
ssap_service = SSAPService()

@router.get("/verdict/{symbol}", response_model=SSAPVerdict)
async def get_ssap_verdict(symbol: str):
    """
    Retrieve the Satellite-to-Sentiment alpha verdict for a specific symbol.
    """
    verdict = await ssap_service.run_analysis(symbol)
    if not verdict:
        raise HTTPException(status_code=404, detail="Analysis failed")
    return verdict

@router.post("/analyze/{symbol}", response_model=SSAPVerdict)
async def trigger_ssap_analysis(symbol: str):
    """
    Trigger a fresh multimodal analysis for a target asset.
    """
    return await ssap_service.run_analysis(symbol)
