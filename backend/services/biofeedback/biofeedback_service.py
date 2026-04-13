import logging
from backend.models.biofeedback_schemas import BiometricReading, TraderSanity, CoachGuidance
from backend.services.biofeedback.health_agent import HealthAgent
from backend.services.biofeedback.guardrail_agent import EmotionalGuardrailAgent, BehavioralCoach

logger = logging.getLogger(__name__)

from backend.services.intelligence_service import IntelligenceService

class BioFeedbackService:
    """
    Orchestrates the Hyper-Personalized Market-Feedback Trader workflow.
    Fuses market-wide physiological data (Volume intensity, VIX) with risk management.
    """
    def __init__(self):
        self.health_agent = HealthAgent()
        self.guardrail_agent = EmotionalGuardrailAgent()
        self.coach = BehavioralCoach()
        self.intel = IntelligenceService()

    async def get_current_status(self) -> dict:
        """
        Polls market 'vitals' and computes the emotional guardrail status for the trader.
        """
        try:
            # Connect to real world: Get market biometrics
            market_vitals = await self.intel.get_market_biometrics()
            
            # Influence sanity analysis by market biometrics
            vitals = await self.health_agent.get_latest_vitals()
            
            # Sync virtual 'vitals' with market fear index
            vitals.bpm = int(70 + (market_vitals.get("fear_index", 15.0))) # Simulate stress
            
            sanity = await self.guardrail_agent.analyze_state(vitals)
            guidance = await self.coach.provide_guidance(sanity)
            
            return {
                "vitals": vitals.dict() if hasattr(vitals, 'dict') else vitals,
                "sanity": sanity.dict() if hasattr(sanity, 'dict') else sanity,
                "guidance": guidance.dict() if hasattr(guidance, 'dict') else guidance,
                "status": "active"
            }
        except Exception as e:
            logger.error(f"BioFeedback sync failure: {str(e)}", exc_info=True)
            # Fallback to safe defaults if agents fail
            return {
                "vitals": {
                    "bpm": 70, "hrv": 60, "respiratory_rate": 14, 
                    "cortisol_index": 0.3, "sleep_quality_score": 0.8
                },
                "sanity": {
                    "emotional_state": "UNKNOWN", "is_guardrail_active": False,
                    "risk_multiplier": 1.0, "fatigue_level": 0.0, "reasoning": "Sync disturbance detected. Defaulting to safe baseline."
                },
                "guidance": {
                    "reflective_question": "Bio-Sync is interrupted. Are you following your core discipline?",
                    "suggested_action": "VERIFY_SYSTEM_LIVENESS",
                    "mistral_analysis": "Diagnostic: System was unable to retrieve real-time biometric stream."
                },
                "status": "degraded",
                "error": str(e)
            }
