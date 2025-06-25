from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import uvicorn
import json
import sys
import os

# Add parent directory of ML_predictor.py to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "utils")))


# Set up correct paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))

# Add utils to path
sys.path.append(os.path.join(project_root, "utils"))


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
def trigger_capture_dialog():
    try:
        flag_path = os.path.join(project_root, "knowledge", "show_dialog.flag")
        with open(flag_path, "w") as f:
            f.write("trigger")
        print("🟢 Dialog trigger flag written.")
        #return "flag_written"
    except Exception as e:
        print("❌ Failed to write flag file:", str(e))
        #return f"error: {e}"



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
