from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import sys
import os

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Try to import your LLM system
try:
    import llm_calls
    LLM_AVAILABLE = True
    print("✅ LLM system loaded successfully")
except ImportError as e:
    print(f"⚠️ LLM system not available: {e}")
    LLM_AVAILABLE = False

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple conversation state
conversation_state = {
    "current_state": "initial",
    "design_data": {},
    "conversation_history": []
}

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    """Direct integration with your LLM system - no complex router"""
    
    if not LLM_AVAILABLE:
        return {"response": "LLM system not available - check imports"}
    
    try:
        user_input = req.message.strip()
        
        # Use your LLM system directly
        current_state = conversation_state["current_state"]
        design_data = conversation_state["design_data"]
        
        print(f"[CHAT] Input: '{user_input}'")
        print(f"[CHAT] State: {current_state}")
        
        # Call your conversation management
        new_state, response, updated_design_data = llm_calls.manage_conversation_state(
            current_state, user_input, design_data
        )
        
        # Update global state
        conversation_state["current_state"] = new_state
        conversation_state["design_data"] = updated_design_data
        
        # Add to history
        conversation_state["conversation_history"].append({
            "user": user_input,
            "assistant": response,
            "state": new_state
        })
        
        print(f"[CHAT] Response: {response[:100]}...")
        
        return {
            "response": response,
            "state": new_state,
            "design_data": updated_design_data,
            "parameters_complete": new_state == "complete",
            "error": False
        }
        
    except Exception as e:
        print(f"[CHAT] Error: {e}")
        return {"response": f"Error: {str(e)}", "error": True}

@app.get("/initial_greeting")
def get_initial_greeting():
    """Get initial greeting from your LLM system"""
    
    if not LLM_AVAILABLE:
        return {"response": "Hello! I'm your design assistant. What would you like to build today?"}
    
    try:
        # Get greeting from your system
        initial_state, greeting, initial_data = llm_calls.manage_conversation_state(
            "initial", "", {}
        )
        
        return {
            "response": greeting,
            "state": initial_state,
            "design_data": initial_data
        }
        
    except Exception as e:
        print(f"[GREETING] Error: {e}")
        return {"response": "Hello! I'm your design assistant. What would you like to build today?"}

@app.get("/conversation_state")
def get_conversation_state():
    """Get current conversation state"""
    return {
        "state": conversation_state["current_state"],
        "design_data": conversation_state["design_data"],
        "parameters_complete": conversation_state["current_state"] == "complete",
        "conversation_history": conversation_state["conversation_history"][-5:]
    }

@app.get("/")
def health_check():
    return {
        "status": "ok", 
        "message": "Simple Modular Design Assistant Server", 
        "llm_available": LLM_AVAILABLE
    }

if __name__ == "__main__":
    print("🚀 Starting Simple Modular Server...")
    print(f"🤖 LLM Available: {LLM_AVAILABLE}")
    uvicorn.run(app, host="127.0.0.1", port=5000)