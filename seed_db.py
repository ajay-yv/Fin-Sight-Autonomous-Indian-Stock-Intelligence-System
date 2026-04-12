import json
from datetime import datetime, timedelta, timezone
from backend.database import SessionLocal, AnalysisRunRow, save_run, save_agent_output, update_run_status, save_synthesis_result
from backend.models.schemas import SynthesisResult

def generate_mock_ohlcv(symbol, days=30):
    import random
    dates = []
    opens = []
    highs = []
    lows = []
    closes = []
    volumes = []
    
    base_price = {"RELIANCE": 2800, "HDFCBANK": 1400, "INFY": 1500}.get(symbol, 1000)
    curr_price = base_price
    
    for i in range(days):
        date_str = (datetime.now(timezone.utc) - timedelta(days=days-i)).strftime("%Y-%m-%d")
        o = curr_price + random.uniform(-10, 10)
        c = o + random.uniform(-20, 20)
        h = max(o, c) + random.uniform(0, 10)
        l = min(o, c) - random.uniform(0, 10)
        v = random.randint(100000, 1000000)
        
        dates.append(date_str)
        opens.append(round(o, 2))
        highs.append(round(h, 2))
        lows.append(round(l, 2))
        closes.append(round(c, 2))
        volumes.append(v)
        curr_price = c
        
    return {
        "dates": dates,
        "opens": opens,
        "highs": highs,
        "lows": lows,
        "closes": closes,
        "volumes": volumes
    }

def seed_demo_run():
    run_id = "demo-run-2026"
    symbols = ["RELIANCE", "HDFCBANK", "INFY"]
    
    print(f"Seeding demo run: {run_id}")
    
    with SessionLocal() as session:
        # Check if run exists
        run = session.scalar(select(AnalysisRunRow).where(AnalysisRunRow.id == run_id))
        if not run:
            save_run(run_id, symbols)
        else:
            print("Run already exists, updating outputs...")

    # 2. Add some mock agent outputs so the dashboard looks populated
    for symbol in symbols:
        # Add OHLCV data for charts
        ohlcv_data = generate_mock_ohlcv(symbol)
        save_agent_output(
            run_id=run_id,
            symbol=symbol,
            agent_name="data_ingestion",
            status="completed",
            signal=None,
            confidence=None,
            reasoning="Market data ingested.",
            data_dict=ohlcv_data
        )

        save_agent_output(
            run_id=run_id,
            symbol=symbol,
            agent_name="technical",
            status="completed",
            signal="BUY",
            confidence=0.85,
            reasoning="Strong bullish trend on daily chart. RSI at 60.",
            data_dict={"rsi": 60, "sma_20": 2500, "verdict": "BUY", "confidence": 0.85}
        )

        save_agent_output(
            run_id=run_id,
            symbol=symbol,
            agent_name="fundamental",
            status="completed",
            signal="BUY",
            confidence=0.75,
            reasoning=f"Strong top-line growth and sector leadership for {symbol}.",
            data_dict={"pe_ratio": 25.4, "debt_to_equity": 0.4, "verdict": "BUY", "confidence": 0.75}
        )

        save_agent_output(
            run_id=run_id,
            symbol=symbol,
            agent_name="sentiment",
            status="completed",
            signal="BUY",
            confidence=0.70,
            reasoning="Positive news sentiment and social media buzz.",
            data_dict={"sentiment_score": 0.65, "verdict": "BUY", "confidence": 0.70}
        )

        save_agent_output(
            run_id=run_id,
            symbol=symbol,
            agent_name="options_flow",
            status="completed",
            signal="BUY",
            confidence=0.82,
            reasoning="Institutional call buying detected in deep OTM strikes. Low PCR.",
            data_dict={
                "symbol": symbol,
                "pcr": 0.65,
                "iv_rank": 42.5,
                "max_pain": 2850.0 if symbol == "RELIANCE" else 1450.0,
                "gex_net": 1.25,
                "oi_change_velocity": 1.4,
                "signal": "BUY",
                "confidence": 0.82,
                "reasoning": "Significant call OI buildup suggests strong support.",
                "key_triggers": ["Block call buy at ₹2900", "PCR drop from 0.8 to 0.65"]
            }
        )

        save_agent_output(
            run_id=run_id,
            symbol=symbol,
            agent_name="social_pulse",
            status="completed",
            signal="BUY",
            confidence=0.78,
            reasoning="Viral social media reach on X and Farcaster. Retail interest spiking.",
            data_dict={
                "symbol": symbol,
                "social_score": 0.85,
                "volume_spike_flag": True,
                "dominant_platform": "Farcaster",
                "top_keywords": ["bullish", "earnings", "undervalued"],
                "sentiment_label": "positive",
                "signal": "BUY",
                "confidence": 0.78,
                "reasoning": "Social volume is 3x the 7-day average.",
                "key_triggers": ["Influencer mention", "Trending in #web3finance"]
            }
        )

        save_agent_output(
            run_id=run_id,
            symbol=symbol,
            agent_name="regulatory",
            status="completed",
            signal="HOLD",
            confidence=0.90,
            reasoning="No ongoing SEBI investigations. Minor filing deadline reminder.",
            data_dict={
                "symbol": symbol,
                "events": [{"category": "Compliance", "risk_score": 1.0, "description": "Routine quarterly filing completed."}],
                "max_risk_score": 1.2,
                "sentiment_impact": "neutral",
                "signal": "HOLD",
                "confidence": 0.90,
                "reasoning": "Regulatory environment is stable for this counter.",
                "key_triggers": ["SEBI approval for new project"]
            }
        )

        save_agent_output(
            run_id=run_id,
            symbol=symbol,
            agent_name="earnings",
            status="completed",
            signal="BUY",
            confidence=0.88,
            reasoning="Alternative data (energy consumption) suggests production beat.",
            data_dict={
                "symbol": symbol,
                "whisper_score": 8.4,
                "surprise_probability": 0.75,
                "concall_tone": "optimistic",
                "alternative_data_proxy": "Satellite Logistics Tracker",
                "signal": "BUY",
                "confidence": 0.88,
                "reasoning": "Whisper numbers are significantly higher than analyst consensus.",
                "key_triggers": ["Inventory drawdown", "Margin expansion guidance"]
            }
        )

        save_agent_output(
            run_id=run_id,
            symbol=symbol,
            agent_name="risk",
            status="completed",
            signal="HOLD",
            confidence=0.80,
            reasoning="Moderate market volatility. Beta within historical range.",
            data_dict={
                 "symbol": symbol,
                 "risk_level": "MEDIUM",
                 "confidence": 0.80,
                 "verdict": "HOLD"
            }
        )
        
        # Add a synthesis result
        result = SynthesisResult(
            symbol=symbol,
            final_verdict="BUY",
            overall_confidence=0.8,
            price_target_pct=5.5,
            summary=f"Strong consensus for {symbol} based on technical and fundamental fusion.",
            detailed_report=f"Detailed report for {symbol} showing high conviction.",
            agent_weights={"technical": 0.4, "fundamental": 0.4, "sentiment": 0.2},
            generated_at=datetime.now(timezone.utc)
        )
        try:
            save_synthesis_result(run_id, result)
        except Exception:
             # Synthesis result might already exist, causing unique constraint if not handled
             print(f"Skipping synthesis save for {symbol} (already exists or error)")

    # 3. Mark run as completed
    update_run_status(run_id, "completed")
    print("Seeding complete.")

if __name__ == "__main__":
    from sqlalchemy import select
    seed_demo_run()
