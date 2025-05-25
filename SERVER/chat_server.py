from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    lm_url = "http://localhost:1234/v1/chat/completions" # LM Studio default folder

    payload = {
        "model": "local-model", # use anyone you want
        "messages": [
            {"role": "system", "content": "You are an assistant embedded in Rhino, be helpful with short answer."},
            {"role": "user", "content": req.message}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(lm_url, json=payload, timeout=20)
        content = response.json()["choices"][0]["message"]["content"]
        return {"response": content}
    except Exception as e:
        print("❌ LLM error:", e)
        return {"response": "Error contacting the local LLM."}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)
