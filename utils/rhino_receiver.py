from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json

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

if __name__ == "__main__":
    print("🌐 Starting Rhino receiver on port 5060...")
    uvicorn.run(app, host="127.0.0.1", port=5060)
