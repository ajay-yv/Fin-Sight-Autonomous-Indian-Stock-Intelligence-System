import asyncio
import os
import sys

# Add project root to path
sys.path.append(r"c:\Users\ajayy\OneDrive\Desktop\FinSight-Autonomous-Indian-Stock-Intelligence-System-main")

from backend.services.ssap_service import SSAPService

async def main():
    service = SSAPService()
    try:
        print("Running SSAP analysis for RELIANCE...")
        verdict = await service.run_analysis("RELIANCE")
        print("Success!")
        print(verdict.model_dump_json(indent=2))
    except Exception as e:
        import traceback
        print("Failed!")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
