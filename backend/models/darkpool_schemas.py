from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class HiddenOrder(BaseModel):
    order_id: str
    symbol: str
    side: str = Field(..., description="BUY or SELL")
    quantity: float = Field(..., description="Fractional quantity")
    price_range: Optional[tuple] = Field(None, description="(min, max) for execution")
    encrypted_payload: str = Field(..., description="Encrypted intent for confidential execution")
    timestamp: datetime
    zkp_solvency_hash: str = Field(..., description="Proof of solvency hash")

class ZKPProof(BaseModel):
    proof_id: str
    order_id: str
    circuit_type: str = Field(..., description="SOLVENCY_CHECK or TRADE_VALIDITY")
    proof_data: str = Field(..., description="SnarkJS proof object string")
    verification_key: str
    status: str = Field("PENDING", description="PENDING, VERIFIED, FAILED")
    generated_at: datetime

class DarkPoolTrade(BaseModel):
    trade_id: str
    symbol: str
    quantity: float
    price: float
    execution_time: datetime
    buyer_order_id: str
    seller_order_id: str
    confidentiality_level: str = "HIGH"
    settlement_hash: str
