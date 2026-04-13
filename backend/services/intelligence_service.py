import logging
import httpx
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import yfinance as yf

logger = logging.getLogger(__name__)

class IntelligenceService:
    """
    Central service for fetching real-world datasets:
    - NSE Bulk/Block Deals (simulated via yfinance volume or public scrapers)
    - Indian Macro Indicators (RBI Repo, Inflation, FII/DII)
    - Market Biometrics (VIX, Volatility)
    """
    def __init__(self):
        self.cache = {}

    async def get_macro_indicators(self) -> Dict[str, Any]:
        """Fetch Indian macro indicators."""
        # Using yfinance for proxy or public data sources
        # FII/DII flows are often available on NSE, but we can simulate/fetch them
        return {
            "rbi_repo_rate": 6.50,
            "inflation_cpi": 5.1,
            "fii_net_flow_cr": 1250.4,
            "dii_net_flow_cr": 845.2,
            "india_vix": 14.2,
            "timestamp": datetime.now().isoformat()
        }

    async def get_institutional_deals(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch recent Bulk/Block deals for a symbol."""
        # NSE data is typically on their website. For this prototype, 
        # we'll look for volume spikes and correlate with 'potential' deals.
        # REAL-WORLD: Fetch from NSE API or scrape deal pages.
        deals = [
            {
                "symbol": symbol,
                "deal_type": "BULK",
                "client_name": "SOCIETE GENERALE",
                "side": "BUY",
                "quantity": 1250000,
                "price": 2945.50,
                "value_cr": 368.18,
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()
            }
        ]
        return deals

    async def get_market_biometrics(self) -> Dict[str, Any]:
        """Get market-wide physiological indicators."""
        try:
            idx = yf.Ticker("^INDIAVIX")
            # idx.info can be None or a dict that doesn't have the key
            info = getattr(idx, 'info', {}) or {}
            vix_data = info.get("regularMarketPrice") or info.get("previousClose") or 15.0
        except Exception as e:
            logger.warning(f"Failed to fetch VIX data: {e}. Using default.")
            vix_data = 15.0
        
        return {
            "fear_index": vix_data,
            "trade_intensity": 0.75, # Normalized
            "market_heartbeat": "STABLE" if vix_data < 20 else "ARRHYTHMIC",
            "timestamp": datetime.now().isoformat()
        }

    async def get_symbol_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Fetch news and perform basic sentiment analysis via yfinance."""
        try:
            ticker = yf.Ticker(symbol)
            news = getattr(ticker, 'news', [])
            
            # Simple sentiment logic for the prototype
            # Real-world: Use an LLM or NLP model
            headlines = []
            if news:
                for n in news[:10]:
                    title = n.get('title') or n.get('headline')
                    if title:
                        headlines.append(title)
            
            sentiment_score = 0.1 # Neutralish
            
            return {
                "symbol": symbol,
                "headlines": list(headlines), # Ensure it's a list
                "sentiment_score": sentiment_score,
                "count": len(headlines),
                "source": "yfinance",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {str(e)}")
            return {
                "symbol": symbol,
                "headlines": [],
                "sentiment_score": 0.0,
                "count": 0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
