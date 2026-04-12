import random
from datetime import datetime
from typing import List
from backend.models.schemas import RWAAssetData, RWAAssetType

class RWADataService:
    """
    Simulated RWA Data Service for AMAPR.
    In 2026, this would connect to Polygon.io RWA feeds and Zoniqx TPaaS APIs.
    """
    
    def __init__(self):
        self.mock_rwas = {
            "RWA_BLR_OFFICE_01": RWAAssetData(
                asset_id="RWA_BLR_OFFICE_01",
                asset_type=RWAAssetType.REAL_ESTATE,
                name="Bangalore Premium Office Space (Tokenized)",
                token_price=1250.45,
                annual_yield=0.082,
                liquidity_score=0.45,
                on_chain_address="0x71C...aB2",
            ),
            "RWA_MUM_WH_02": RWAAssetData(
                asset_id="RWA_MUM_WH_02",
                asset_type=RWAAssetType.REAL_ESTATE,
                name="Mumbai Grade-A Warehouse Token",
                token_price=540.20,
                annual_yield=0.095,
                liquidity_score=0.30,
                on_chain_address="0x82D...3C4",
            ),
            "RWA_CREDIT_SME_IND": RWAAssetData(
                asset_id="RWA_CREDIT_SME_IND",
                asset_type=RWAAssetType.PRIVATE_CREDIT,
                name="Indian MSME Credit Pool (Junior Tranche)",
                token_price=10.0,
                annual_yield=0.14,
                liquidity_score=0.15,
                on_chain_address="0x93E...4D5",
            ),
            "RWA_GOLD_DGL_01": RWAAssetData(
                asset_id="RWA_GOLD_DGL_01",
                asset_type=RWAAssetType.COMMODITIES,
                name="Pax Gold Digital Proxy (NSE-linked)",
                token_price=6400.0,
                annual_yield=0.0,
                liquidity_score=0.95,
                on_chain_address="0xA4F...5E6",
            )
        }

    def get_asset_details(self, asset_id: str) -> RWAAssetData:
        return self.mock_rwas.get(asset_id)

    def list_all_rwas(self) -> List[RWAAssetData]:
        return list(self.mock_rwas.values())

    def get_live_price(self, asset_id: str) -> float:
        # Simulate slight volatility
        base = self.mock_rwas.get(asset_id).token_price
        return base * (1 + random.uniform(-0.005, 0.005))
