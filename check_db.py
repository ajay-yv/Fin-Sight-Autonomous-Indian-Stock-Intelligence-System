from backend.database import SessionLocal, AgentOutputRow
from sqlalchemy import select

def check_data():
    run_id = "demo-run-2026"
    print(f"Checking data for run: {run_id}")
    with SessionLocal() as session:
        rows = session.scalars(
            select(AgentOutputRow).where(AgentOutputRow.run_id == run_id)
        ).all()
        print(f"Total agent outputs: {len(rows)}")
        for r in rows:
            print(f"  Symbol: {r.symbol}, Agent: {r.agent_name}, Data present: {r.data_json is not None}")

if __name__ == "__main__":
    check_data()
