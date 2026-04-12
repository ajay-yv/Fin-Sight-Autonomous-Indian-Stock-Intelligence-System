from typing import List
from backend.models.schemas import PortfolioState, RebalanceAction, PortfolioAsset

class ExecutionEngine:
    """
    Simulated Execution Engine for 2026 AMAPR.
    In production, this would interface with NSE broker APIs and RWA smart contracts.
    """
    
    def apply_actions(self, state: PortfolioState, actions: List[RebalanceAction]) -> PortfolioState:
        new_assets = {a.symbol: a for a in state.assets}
        new_cash = state.cash_balance
        
        for action in actions:
            if action.action == "BUY":
                # Check for existing
                asset = new_assets.get(action.symbol)
                cost = action.quantity * 1000 # Mock price
                if new_cash >= cost:
                    new_cash -= cost
                    if asset:
                        asset.quantity += action.quantity
                        # Average out price logic omitted for simplicity
                    else:
                        # New asset
                        new_assets[action.symbol] = PortfolioAsset(
                            symbol=action.symbol,
                            asset_type="equity" if "RWA" not in action.symbol else "rwa",
                            quantity=action.quantity,
                            avg_buy_price=1000.0,
                            current_price=1000.0,
                            value_in_inr=cost,
                            tax_basis_date=datetime.utcnow()
                        )
            
            elif action.action == "SELL":
                asset = new_assets.get(action.symbol)
                if asset and asset.quantity >= action.quantity:
                    revenue = action.quantity * asset.current_price
                    new_cash += revenue
                    asset.quantity -= action.quantity
                    if asset.quantity <= 0:
                        del new_assets[action.symbol]

        return PortfolioState(
            portfolio_id=state.portfolio_id,
            assets=list(new_assets.values()),
            cash_balance=new_cash,
            timestamp=datetime.utcnow()
        )
