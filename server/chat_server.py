from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import sys
import os
import json
import time
import threading
from pathlib import Path

# Try to import watchdog for file monitoring
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("⚠️ Watchdog not available - file monitoring disabled")

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
# try:
#     import llm_calls
#     print("✅ llm_calls imported:", dir(llm_calls))  # 🔍 Check what it contains
#     assert hasattr(llm_calls, "manage_conversation_state"), "Missing function: manage_conversation_state"
#     assert hasattr(llm_calls, "answer_user_query"), "Missing function: answer_user_query"
#     LLM_AVAILABLE = True
#     print("✅ LLM system loaded successfully")
# except Exception as e:
#     print(f"⚠️ LLM system not available: {e}")
#     llm_calls = None
#     LLM_AVAILABLE = False


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global conversation state + Phase 2 detection
conversation_state = {
    "current_state": "initial",
    "design_data": {},
    "conversation_history": [],
    "phase": 1
}

# Phase 2 detection
phase2_activated = False
file_observer = None

# File watcher for automatic Phase 2 activation
class MLFileWatcher(FileSystemEventHandler):
    def __init__(self):
        self.last_modified = {}
    
    def on_modified(self, event):
        if event.is_directory:
            return
            
        file_name = Path(event.src_path).name
        if file_name != "ml_output.json":
            return
            
        current_time = time.time()
        if file_name in self.last_modified:
            if current_time - self.last_modified[file_name] < 2:  # 2 second debounce
                return
                
        self.last_modified[file_name] = current_time
        
        print(f"🔄 File watcher detected change in {file_name}")
        
        # AUTOMATICALLY remove the processed flag when ML output changes
        try:
            flag_file = "knowledge/ml_processed.flag"
            if os.path.exists(flag_file):
                os.remove(flag_file)
                print("✅ Automatically removed processed flag - ready for Phase 2")
        except Exception as e:
            print(f"⚠️ Could not remove processed flag: {e}")
        
        # Check if we should activate Phase 2
        if (not phase2_activated and 
            conversation_state.get("current_state") == "complete" and 
            check_for_ml_output()):
            
            self.activate_phase2_automatically()
    
    def activate_phase2_automatically(self):
        """Activate Phase 2 when ML file changes"""
        global phase2_activated, conversation_state
        
        try:
            print("🔄 File change detected - checking Phase 2 activation...")
            
            # Check if conditions are met
            phase1_complete = conversation_state.get("current_state") == "complete"
            can_activate = check_for_ml_output()
            
            print(f"[AUTO ACTIVATION] Phase 1 complete: {phase1_complete}")
            print(f"[AUTO ACTIVATION] Can activate: {can_activate}")
            print(f"[AUTO ACTIVATION] Already activated: {phase2_activated}")
            
            if phase1_complete and can_activate and not phase2_activated:
                phase2_activated = True
                conversation_state["phase"] = 2
                mark_ml_output_processed()
                
                # Add automatic message to conversation history
                auto_message = {
                    "user": "[SYSTEM]",
                    "assistant": "🎯 Phase 2 activated automatically! ML analysis updated. You can now ask about embodied carbon, improvements, or design changes.",
                    "phase": 2,
                    "trigger": "file_change",
                    "timestamp": time.time()
                }
                conversation_state["conversation_history"].append(auto_message)
                
                # Terminal message
                print("=" * 60)
                print("🎯 PHASE 2 ACTIVATED AUTOMATICALLY!")
                print("   Triggered by ML file change")
                print("   User can now ask about:")
                print("   • Embodied carbon analysis")
                print("   • Design improvements") 
                print("   • Material changes")
                print("=" * 60)
            else:
                print("❌ Phase 2 activation conditions not met")
            
        except Exception as e:
            print(f"❌ Error activating Phase 2: {e}")

def start_file_watcher():
    """Start file watcher for ML output changes"""
    global file_observer
    
    if not WATCHDOG_AVAILABLE:
        print("📁 File watcher not available - install watchdog: pip install watchdog")
        return None
    
    try:
        os.makedirs("knowledge", exist_ok=True)
        
        event_handler = MLFileWatcher()
        file_observer = Observer()
        file_observer.schedule(event_handler, "knowledge", recursive=False)
        file_observer.start()
        
        print("📁 File watcher started - monitoring knowledge/ml_output.json")
        return file_observer
        
    except Exception as e:
        print(f"⚠️ Could not start file watcher: {e}")
        return None

def check_for_ml_output():
    """Check if ML output file exists and has been processed"""
    ml_file = "knowledge/ml_output.json"
    processed_flag = "knowledge/ml_processed.flag"
    
    # Debug logging
    ml_exists = os.path.exists(ml_file)
    flag_exists = os.path.exists(processed_flag)
    
    print(f"[ML CHECK] ML file exists: {ml_exists}")
    print(f"[ML CHECK] Processed flag exists: {flag_exists}")
    
    # Only trigger Phase 2 if:
    # 1. ML output exists AND
    # 2. We haven't processed it yet (no flag file)
    result = ml_exists and not flag_exists
    print(f"[ML CHECK] Should trigger Phase 2: {result}")
    
    return result

def mark_ml_output_processed():
    """Mark ML output as processed to avoid re-triggering Phase 2"""
    try:
        os.makedirs("knowledge", exist_ok=True)
        with open("knowledge/ml_processed.flag", "w") as f:
            f.write(str(time.time()))
    except Exception as e:
        print(f"Warning: Could not create processed flag: {e}")

def classify_phase2_intent(user_input):
    """Simple intent classification for Phase 2"""
    input_lower = user_input.lower()
    
    if any(word in input_lower for word in ["carbon", "embodied", "gwp", "environmental", "emissions"]):
        return "carbon_query"
    elif any(word in input_lower for word in ["improve", "optimize", "reduce", "better", "recommend"]):
        return "improvement_suggestion"
    elif any(word in input_lower for word in ["change", "switch", "modify", "update", "replace"]):
        return "design_change"
    else:
        return "general_query"

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    """Enhanced LLM system with full Phase 2 functionality"""
    global phase2_activated, conversation_state
    
    if not LLM_AVAILABLE:
        return {"response": "LLM system not available - check imports"}
    
    try:
        user_input = req.message.strip()
        
        print(f"[CHAT] Input: '{user_input}'")
        print(f"[CHAT] Phase: {conversation_state.get('phase', 1)}")
        print(f"[CHAT] Phase2 activated: {phase2_activated}")
        print(f"[CHAT] ML file exists: {os.path.exists('knowledge/ml_output.json')}")
        
        # Check for Phase 2 activation ONLY if Phase 1 is complete
        if (not phase2_activated and 
            conversation_state.get("current_state") == "complete" and 
            check_for_ml_output()):
            
            phase2_activated = True
            conversation_state["phase"] = 2
            mark_ml_output_processed()  # Mark as processed
            
            # Terminal message
            print("=" * 60)
            print("🎯 PHASE 2 ACTIVATED!")
            print("   ML analysis detected and processed")
            print("   User can now ask about:")
            print("   • Embodied carbon analysis")
            print("   • Design improvements") 
            print("   • Material changes")
            print("=" * 60)
            
            return {
                "response": "🎯 Phase 2 activated! ML analysis detected. You can now ask about:\n• Embodied carbon analysis\n• Design improvements\n• Material changes",
                "phase": 2,
                "state": "analysis",
                "triggered_by": "ml_output_detected",
                "error": False
            }
        
        # ===== PHASE 2 PROCESSING =====
        if phase2_activated and conversation_state.get("phase") == 2:
            print("🔍 [PHASE 2] Starting Phase 2 processing...")
            
            try:
                # Classify intent for Phase 2
                intent = classify_phase2_intent(user_input)
                print(f"🔍 [PHASE 2] Intent classified as: {intent}")
                
                # Get current design data
                design_data = conversation_state.get("design_data", {})
                print(f"🔍 [PHASE 2] Design data keys: {list(design_data.keys())}")
                
                # Load ML results from file - FORCE LOAD
                print("🔍 [PHASE 2] Starting ML data loading...")
                ml_data = {}
                ml_file = "knowledge/ml_output.json"
                
                print(f"🔍 [PHASE 2] Checking file: {ml_file}")
                print(f"🔍 [PHASE 2] File exists: {os.path.exists(ml_file)}")
                
                if os.path.exists(ml_file):
                    try:
                        with open(ml_file, 'r') as f:
                            ml_data = json.load(f)
                        print(f"✅ [PHASE 2] Successfully loaded ML data with keys: {list(ml_data.keys())}")
                        
                        if 'carbon' in ml_data:
                            print(f"✅ [PHASE 2] Carbon data found: {ml_data['carbon']}")
                        if 'energy' in ml_data:
                            print(f"✅ [PHASE 2] Energy data found: {ml_data['energy']}")
                            
                    except Exception as e:
                        print(f"❌ [PHASE 2] Error reading ML file: {e}")
                        return {
                            "response": f"❌ Error reading ML analysis file: {str(e)}",
                            "phase": 2,
                            "error": False
                        }
                else:
                    print("❌ [PHASE 2] ML output file does not exist!")
                    return {
                        "response": "❌ No ML analysis data found. Please ensure the ML analysis has completed and ml_output.json exists.",
                        "phase": 2,
                        "error": False
                    }
                
                # Create comprehensive data package for Phase 2 functions
                comprehensive_data = {
                    # Original design parameters
                    "building_parameters": design_data,
                    
                    # ML Analysis Results
                    "carbon_analysis": ml_data.get('carbon', {}),
                    "energy_analysis": ml_data.get('energy', {}),
                    
                    # Full ML data
                    "ml_results": ml_data,
                    
                    # Metadata
                    "analysis_complete": True,
                    "data_source": "ml_output.json"
                }
                
                print(f"✅ [PHASE 2] Comprehensive data package created:")
                print(f"   - Building parameters: {list(comprehensive_data['building_parameters'].keys())}")
                print(f"   - Carbon analysis: {list(comprehensive_data['carbon_analysis'].keys())}")
                print(f"   - Energy analysis: {list(comprehensive_data['energy_analysis'].keys())}")
                
                # Handle different intents with proper data
                print(f"🔍 [PHASE 2] Calling LLM function for intent: {intent}")
                
                if intent == "carbon_query":
                    response = llm_calls.answer_user_query(user_input, comprehensive_data)
                elif intent == "improvement_suggestion":
                    response = llm_calls.suggest_improvements(user_input, comprehensive_data)
                elif intent == "design_change":
                    response = llm_calls.suggest_change(user_input, comprehensive_data)
                else:
                    response = llm_calls.answer_user_query(user_input, comprehensive_data)
                
                print(f"✅ [PHASE 2] LLM response received: {response[:200]}...")
                
                # Add to conversation history
                conversation_state["conversation_history"].append({
                    "user": user_input,
                    "assistant": response,
                    "phase": 2,
                    "intent": intent,
                    "timestamp": time.time()
                })
                
                return {
                    "response": response,
                    "phase": 2,
                    "state": "analysis",
                    "intent": intent,
                    "design_data": comprehensive_data,
                    "error": False
                }
                
            except Exception as e:
                print(f"❌ [PHASE 2] Major error: {e}")
                import traceback
                traceback.print_exc()
                return {
                    "response": f"❌ Phase 2 processing error: {str(e)}. Please check server logs.",
                    "phase": 2,
                    "error": True
                }
        
        # ===== PHASE 1 PROCESSING =====
        current_state = conversation_state["current_state"]
        design_data = conversation_state["design_data"]
        
        print(f"[PHASE 1] State: {current_state}")
        
        # Call your conversation management
        new_state, response, updated_design_data = llm_calls.manage_conversation_state(
            current_state, user_input, design_data
        )
        
        # Update global state
        conversation_state["current_state"] = new_state
        conversation_state["design_data"] = updated_design_data
        conversation_state["phase"] = 1
        
        # Add to history
        conversation_state["conversation_history"].append({
            "user": user_input,
            "assistant": response,
            "state": new_state,
            "phase": 1,
            "timestamp": time.time()
        })
        
        print(f"[PHASE 1] Response: {response[:100]}...")
        
        # Check if Phase 1 is complete
        if new_state == "complete":
            response += "\n\n✅ Phase 1 complete! When ML analysis runs, Phase 2 will activate automatically."
        
        return {
            "response": response,
            "state": new_state,
            "phase": 1,
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
            "design_data": initial_data,
            "phase": 1
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
        "phase": conversation_state.get("phase", 1),
        "phase2_activated": phase2_activated,
        "ml_output_exists": os.path.exists("knowledge/ml_output.json"),
        "ml_can_trigger": check_for_ml_output(),
        "file_watcher_active": file_observer is not None and file_observer.is_alive() if WATCHDOG_AVAILABLE else False,
        "parameters_complete": conversation_state["current_state"] == "complete",
        "conversation_history": conversation_state["conversation_history"][-5:]
    }

@app.post("/trigger_phase2")
def trigger_phase2():
    """Manually trigger Phase 2 for testing"""
    global phase2_activated, conversation_state
    
    try:
        phase2_activated = True
        conversation_state["phase"] = 2
        conversation_state["current_state"] = "analysis"
        
        return {
            "message": "Phase 2 activated manually",
            "phase": 2,
            "success": True
        }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }

@app.post("/reset_ml_flag")
def reset_ml_flag():
    """Reset ML processed flag to test Phase 2 activation"""
    try:
        flag_file = "knowledge/ml_processed.flag"
        if os.path.exists(flag_file):
            os.remove(flag_file)
        
        return {
            "message": "ML processed flag reset - Phase 2 will activate on next completed conversation",
            "success": True
        }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }

@app.post("/debug_phase2_data")
def debug_phase2_data():
    """Debug endpoint to see exactly what data Phase 2 functions receive"""
    try:
        # Get current design data
        design_data = conversation_state.get("design_data", {})
        
        # Load ML results
        ml_data = {}
        ml_file = "knowledge/ml_output.json"
        if os.path.exists(ml_file):
            with open(ml_file, 'r') as f:
                ml_data = json.load(f)
        
        # Combine data (same as Phase 2)
        combined_data = {
            "building_parameters": design_data,
            "carbon_analysis": ml_data.get('carbon', {}),
            "energy_analysis": ml_data.get('energy', {}),
            "ml_results": ml_data,
            "analysis_complete": True,
            "data_source": "ml_output.json"
        }
        
        return {
            "design_data": design_data,
            "ml_data": ml_data,
            "combined_data": combined_data,
            "data_summary": {
                "has_ml_file": os.path.exists(ml_file),
                "ml_data_keys": list(ml_data.keys()) if ml_data else [],
                "carbon_available": bool(ml_data.get('carbon')),
                "energy_available": bool(ml_data.get('energy')),
                "design_params": list(design_data.keys())
            }
        }
    except Exception as e:
        return {
            "error": str(e)
        }

@app.get("/")
def health_check():
    return {
        "status": "ok", 
        "message": "Rhino Copilot Server with Full Phase 2", 
        "llm_available": LLM_AVAILABLE,
        "phase": conversation_state.get("phase", 1),
        "phase2_activated": phase2_activated,
        "ml_output_exists": os.path.exists("knowledge/ml_output.json"),
        "watchdog_available": WATCHDOG_AVAILABLE
    }

if __name__ == "__main__":
    print("🚀 Starting Rhino Copilot Server with Full Phase 2...")
    print(f"🤖 LLM Available: {LLM_AVAILABLE}")
    print(f"📁 ML Output Exists: {os.path.exists('knowledge/ml_output.json')}")
    print(f"🔍 Watchdog Available: {WATCHDOG_AVAILABLE}")
    
    # Start file watcher in background thread
    if WATCHDOG_AVAILABLE:
        def start_watcher():
            start_file_watcher()
        
        watcher_thread = threading.Thread(target=start_watcher, daemon=True)
        watcher_thread.start()
        time.sleep(1)  # Give it a moment to start
    
    uvicorn.run(app, host="127.0.0.1", port=5001) # later replace port=free_port





# from utils.knowledge_compiler import KnowledgeCompiler
# KnowledgeCompiler()