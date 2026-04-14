from backend.main import app
import uvicorn

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        import traceback
        traceback.print_exc()
