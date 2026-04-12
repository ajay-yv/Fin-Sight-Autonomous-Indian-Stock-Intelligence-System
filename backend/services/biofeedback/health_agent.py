import random
import logging
from datetime import datetime
from backend.models.biofeedback_schemas import BiometricReading

logger = logging.getLogger(__name__)

class HealthAgent:
    """
    Ingests and analyzes real-time biometric data from wearables.
    In 2026, uses high-resolution HRV and cortisol proxies to monitor cognitive load.
    """
    def __init__(self):
        self.hrv_baseline = 65.0 # ms
        self.bpm_baseline = 70

    async def get_latest_vitals(self) -> BiometricReading:
        """
        Simulates data ingestion from Oura/HealthKit APIs.
        """
        logger.info("Ingesting live biometric data...")
        
        # Simulate physiological fluctuations
        # High stress simulation: HRV drops, BPM rises
        is_stressed = random.random() > 0.7
        
        if is_stressed:
            current_hrv = self.hrv_baseline * random.uniform(0.5, 0.75)
            current_bpm = self.bpm_baseline + random.randint(15, 30)
            cortisol = random.uniform(0.6, 0.9)
        else:
            current_hrv = self.hrv_baseline * random.uniform(0.9, 1.2)
            current_bpm = self.bpm_baseline + random.randint(-5, 10)
            cortisol = random.uniform(0.1, 0.4)

        return BiometricReading(
            timestamp=datetime.now(),
            hrv=current_hrv,
            bpm=current_bpm,
            respiratory_rate=random.uniform(12, 18),
            cortisol_index=cortisol,
            sleep_quality_score=random.uniform(0.6, 0.9)
        )
