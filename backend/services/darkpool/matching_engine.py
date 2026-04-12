import logging
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from backend.models.darkpool_schemas import HiddenOrder, DarkPoolTrade, ZKPProof

logger = logging.getLogger(__name__)

class MatchingEngine:
    """
    Confidential Matching Engine for the Dark Pool.
    In 2026, this runs inside a Confidential Enclave (TEE) like Oasis Sapphire.
    Order details are only visible to the TEE matching logic.
    """
    def __init__(self):
        self.buy_side: List[HiddenOrder] = []
        self.sell_side: List[HiddenOrder] = []

    async def submit_order(self, order: HiddenOrder) -> Optional[DarkPoolTrade]:
        """
        Adds an order to the confidential book and attempts a P2P match.
        """
        logger.info(f"Confidential Enclave: Processing {order.side} order for {order.symbol}")
        
        target_side = self.sell_side if order.side == "BUY" else self.buy_side
        matching_side = self.buy_side if order.side == "BUY" else self.sell_side
        
        # Simple crossing logic (Mock)
        for other in target_side:
            if other.symbol == order.symbol:
                # In a real engine, we'd check prices inside the enclave
                # Here we assume a match if symbols match for fractional shares
                match_qty = min(order.quantity, other.quantity)
                
                trade = DarkPoolTrade(
                    trade_id=f"TRD-{uuid.uuid4().hex[:8]}",
                    symbol=order.symbol,
                    quantity=match_qty,
                    price=1500.25, # Mock price
                    execution_time=datetime.now(),
                    buyer_order_id=order.order_id if order.side == "BUY" else other.order_id,
                    seller_order_id=order.order_id if order.side == "SELL" else other.order_id,
                    settlement_hash=f"SETTLE-{uuid.uuid4().hex[:12]}"
                )
                
                # Remove or update orders after match
                target_side.remove(other)
                if order.quantity > match_qty:
                    order.quantity -= match_qty
                    matching_side.append(order)
                
                logger.info(f"Match Executed in Enclave: {trade.trade_id}")
                return trade
        
        # No immediate match, add to book
        matching_side.append(order)
        return None
