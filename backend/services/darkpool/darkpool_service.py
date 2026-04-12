import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict
from backend.models.darkpool_schemas import HiddenOrder, DarkPoolTrade, ZKPProof
from backend.services.darkpool.zkp_service import ZKPService
from backend.services.darkpool.matching_engine import MatchingEngine

logger = logging.getLogger(__name__)

class DarkPoolService:
    """
    Orchestrates the Decentralized Dark Pool workflow.
    Ensures ZKP verification before confidential matching.
    """
    def __init__(self):
        self.zkp = ZKPService()
        self.engine = MatchingEngine()
        self.trades_history: List[DarkPoolTrade] = []

    async def submit_private_order(self, symbol: str, side: str, quantity: float) -> Dict:
        """
        Submits an order through the privacy-preserving pipeline.
        """
        order_id = str(uuid.uuid4())
        
        # Phase 1: ZKP Proof of Solvency
        # Mock balance check
        user_balance = 50000.0
        required = quantity * 1500.0 # Mock price
        
        proof = await self.zkp.generate_solvency_proof(order_id, user_balance, required)
        
        if not self.zkp.verify_proof(proof):
            return {"status": "FAILED", "reason": "ZKP Solvency Verification Failed"}

        # Phase 2: Confidential Submission
        order = HiddenOrder(
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            encrypted_payload="ENC_PROTOCOL_V1_" + uuid.uuid4().hex,
            timestamp=datetime.now(),
            zkp_solvency_hash=proof.proof_id
        )
        
        trade = await self.engine.submit_order(order)
        
        if trade:
            self.trades_history.append(trade)
            return {"status": "EXECUTED", "trade": trade, "proof": proof}
        
        return {"status": "PENDING_IN_ENCLAVE", "order_id": order_id, "proof": proof}

    def get_market_volume(self) -> float:
        """Returns the total confidential volume processed."""
        return sum(t.quantity for t in self.trades_history)
