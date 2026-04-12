import logging
from backend.models.biofeedback_schemas import BiometricReading, TraderSanity, CoachGuidance
from backend.services.biofeedback.health_agent import HealthAgent
from backend.services.biofeedback.guardrail_agent import EmotionalGuardrailAgent, BehavioralCoach

logger = logging.getLogger(__name__)

class BioFeedbackService:
    """
    Orchestrates the Hyper-Personalized Bio-Feedback Trader workflow.
    Fuses physiological data with automated risk management.
    """
    def __init__(self):
        self.health_agent = HealthAgent()
        self.guardrail_agent = EmotionalGuardrailAgent()
        self.coach = BehavioralCoach()

    async def get_current_status(self) -> dict:
        """
        Polls health data and computes the emotional guardrail status.
        """
        vitals = await self.health_agent.get_latest_vitals()
        sanity = await self.guardrail_agent.analyze_state(vitals)
        guidance = await self.coach.provide_guidance(sanity)
        
        return {
            "vitals": vitals,
            "sanity": sanity,
            "guidance": guidance
        }
