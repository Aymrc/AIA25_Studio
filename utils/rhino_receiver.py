from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import uvicorn
import json
import sys
import os
import time


# Add parent directory of ML_predictor.py to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "utils")))


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/geometry")
async def receive_geometry(request: Request):
    try:
        data = await request.json()
        print("✅ Received geometry data:")
        print(json.dumps(data, indent=2))
        return {"status": "ok"}
    except Exception as e:
        print("❌ Error:", str(e))
        return {"status": "error", "message": str(e)}
    


@app.get("/screenshot/", response_class=PlainTextResponse)
def manual_screenshot():
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))
        from ML_predictor import create_manual_iteration

        # 1. Determine iteration ID first
        success, next_id_or_error = create_manual_iteration(get_id_only=True)
        if not success:
            return f"error: {next_id_or_error}"
        version_id = next_id_or_error  # e.g. "I4"

        # 2. Retry writing the flag file, ensuring listener sees it
        base_dir = os.path.dirname(os.path.dirname(__file__))
        flag_path = os.path.join(base_dir, "knowledge", "capture_now.txt")

        # Wait up to 5 seconds for listener to get ready
        for _ in range(5):
            if os.path.exists(flag_path):
                os.remove(flag_path)  # Clean up stale
            try:
                with open(flag_path, "w") as f:
                    f.write(version_id)
                print(f"📸 Flag written with ID: {version_id}")
                break
            except Exception as e:
                print("Retrying flag write...")
                time.sleep(1)
        else:
            return "❌ Failed to write flag file after retries."

        # 3. Wait for Rhino to capture
        time.sleep(6)

        # 4. Finalize iteration
        success, message = create_manual_iteration(use_existing_id=version_id)
        return message if success else f"error: {message}"

    except Exception as e:
        return f"error: {e}"





if __name__ == "__main__":
    try:
        print("🌐 Starting Rhino receiver on port 5005...")
        uvicorn.run(app, host="127.0.0.1", port=5005)
    except Exception as e:
        with open("rhino_listener_error.log", "w") as log:
            import traceback
            log.write("🚨 Rhino listener crashed:\n")
            log.write(traceback.format_exc())
        print("❌ Rhino listener crashed. See rhino_listener_error.log for details.")


