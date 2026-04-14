from fastapi import APIRouter, HTTPException
from backend.services.biofeedback.biofeedback_service import BioFeedbackService

router = APIRouter(prefix="/biofeedback", tags=["Bio-Feedback"])
bio_service = BioFeedbackService()

@router.get("/status")
async def get_trader_bio_status():
    """
    Retrieve real-time biometric vitals and emotional guardrail status.
    """
    try:
        return await bio_service.get_current_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refresh")
async def refresh_bio_sync():
    """
    Triggers a fresh sync with wearable devices and re-evaluates risk.
    """
    return await bio_service.get_current_status()
