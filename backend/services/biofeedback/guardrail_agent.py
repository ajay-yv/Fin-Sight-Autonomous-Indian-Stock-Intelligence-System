import logging
from datetime import datetime
from backend.models.biofeedback_schemas import BiometricReading, TraderSanity, CoachGuidance

logger = logging.getLogger(__name__)

class EmotionalGuardrailAgent:
    """
    Analyzes biometric anomalies to apply 'Emotional Guardrails'.
    If stress or fatigue is detected, it reduces trading risk parameters.
    """
    def __init__(self):
        self.name = "GuardrailIntelligence"

    async def analyze_state(self, vitals: BiometricReading) -> TraderSanity:
        """
        Determines the trader's emotional sanity and active risk multiplier.
        """
        # Logic: Low HRV (< 40ms) or High Cortisol (> 0.7) triggering Defensive Mode
        is_stressed = vitals.hrv < 45 or vitals.cortisol_index > 0.7
        fatigue = 1.0 - vitals.sleep_quality_score
        
        risk_multiplier = 1.0
        state = "CALM"
        reasoning = "Physiological markers are within healthy baselines. Full risk capacity authorized."
        
        if is_stressed:
            risk_multiplier = 0.5
            state = "ANXIOUS"
            reasoning = (
                f"Heart Rate Variability is low ({vitals.hrv:.1f}ms) and cortisol is elevated. "
                "Detecting acute stress response. Reducing risk exposure by 50% to prevent irrational execution."
            )
        elif fatigue > 0.4:
            risk_multiplier = 0.75
            state = "FATIGUED"
            reasoning = (
                f"Cognitive fatigue detected (Sleep Score: {vitals.sleep_quality_score:.2f}). "
                "Reaction times may be impaired. Defensive trading mode active."
            )

        return TraderSanity(
            timestamp=datetime.now(),
            fatigue_level=fatigue,
            emotional_state=state,
            risk_multiplier=risk_multiplier,
            is_guardrail_active=is_stressed or fatigue > 0.4,
            reasoning=reasoning
        )

class BehavioralCoach:
    """
    Mistral-based behavioral coach providing reflective feedback.
    """
    async def provide_guidance(self, insanity: TraderSanity) -> CoachGuidance:
        questions = {
            "ANXIOUS": "You're showing signs of acute stress. Are you reacting to a specific market move or external pressure?",
            "FATIGUED": "Your cognitive load is high. Have you considered that your best trade today might be to step away?",
            "CALM": "You're in a peak performance state. How does your current focus feel compared to previous sessions?"
        }
        
        actions = {
            "ANXIOUS": "REDUCE_SIZE_AND_BREATHE",
            "FATIGUED": "CLOSE_EXPOSURE_AND_REST",
            "CALM": "STAY_DISCIPLINED"
        }

        return CoachGuidance(
            guidance_id=f"COACH-{datetime.now().strftime('%H%M%S')}",
            timestamp=datetime.now(),
            sentiment_context=insanity.emotional_state,
            reflective_question=questions.get(insanity.emotional_state, "How is your focus?"),
            suggested_action=actions.get(insanity.emotional_state, "NONE"),
            mistral_analysis=f"Based on your current physiological state ({insanity.emotional_state}), your risk profile has been adjusted to {insanity.risk_multiplier*100}%."
        )
