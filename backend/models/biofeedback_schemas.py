from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class BiometricReading(BaseModel):
    timestamp: datetime
    hrv: float = Field(..., description="Heart Rate Variability in ms")
    bpm: int = Field(..., description="Beats Per Minute")
    respiratory_rate: float
    cortisol_index: float = Field(..., ge=0, le=1, description="Simulated stress hormone proxy")
    sleep_quality_score: float = Field(..., ge=0, le=1)

class TraderSanity(BaseModel):
    timestamp: datetime
    fatigue_level: float = Field(..., ge=0, le=1)
    emotional_state: str = Field(..., description="e.g., CALM, ANXIOUS, AGGRESSIVE, FATIGUED")
    risk_multiplier: float = Field(1.0, ge=0.1, le=1.0, description="Risk reduction factor (1.0 = normal, 0.5 = defensive)")
    is_guardrail_active: bool
    reasoning: str

class CoachGuidance(BaseModel):
    guidance_id: str
    timestamp: datetime
    sentiment_context: str
    reflective_question: str
    suggested_action: str = Field(..., description="e.g., WALK_AWAY, REDUCE_SIZE, MEDITATE")
    mistral_analysis: str
