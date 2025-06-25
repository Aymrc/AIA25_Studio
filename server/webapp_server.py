from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import webbrowser
import uvicorn
import json

app = FastAPI()

# === Set up paths ===
base_dir = Path(__file__).parent.parent
webapp_dir = base_dir / "ui" / "cherry"
static_dir = webapp_dir  # includes script.js, style.css
data_dir = base_dir / "knowledge" / "iterations"

# === Serve static frontend ===
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/images", StaticFiles(directory=data_dir), name="images")
app.mount("/knowledge/iterations", StaticFiles(directory=data_dir), name="jsons")

# === Serve main HTML file ===
@app.get("/", response_class=HTMLResponse)
def serve_index():
    return (webapp_dir / "index.html").read_text(encoding="utf-8")

# === API: serve summarized gwp_data ===
@app.get("/api/gwp_data")
def get_gwp_data():
    items = []
    for file in data_dir.glob("*.json"):
        try:
            with open(file, encoding="utf-8") as f:
                data = json.load(f)
                items.append({
                    "version": file.stem,
                    "outputs": data.get("outputs", {})
                })
        except Exception as e:
            print(f"Failed to load {file}: {e}")
    return items

# === Trigger browser launch ===
@app.get("/api/open_cherry")
def open_cherry():
    url = "http://localhost:5002"
    try:
        webbrowser.open(url)
        return {"status": "launched", "url": url}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# === Launch ===
if __name__ == "__main__":
    print("🚀 Launching WebApp server on port 5002...")
    uvicorn.run(app, host="127.0.0.1", port=5002)
