from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request
from pydantic import BaseModel
import uvicorn
import sys
import os
import json
import time
import threading
from pathlib import Path
import socket
import subprocess
import re

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


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
 
#IMPORTANT = PHASE DETECTION
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
#class MLFileWatcher(FileSystemEventHandler):
    #def __init__(self):
    #     self.last_modified = {}
    
    # def on_modified(self, event):
    #     if event.is_directory:
    #         return
            
    #     file_name = Path(event.src_path).name
    #     if file_name != "ml_output.json":
    #         return
            
    #     current_time = time.time()
    #     if file_name in self.last_modified:
    #         if current_time - self.last_modified[file_name] < 2:  # 2 second debounce
    #             return
                
    #     self.last_modified[file_name] = current_time
        
    #     print(f"🔄 File watcher detected change in {file_name}")
        
    #     # AUTOMATICALLY remove the processed flag when ML output changes
    #     try:
    #         flag_file = "knowledge/ml_processed.flag"
    #         if os.path.exists(flag_file):
    #             os.remove(flag_file)
    #             print("✅ Automatically removed processed flag - ready for Phase 2")
    #     except Exception as e:
    #         print(f"⚠️ Could not remove processed flag: {e}")
        
    #     # Check if we should activate Phase 2
    #     if (not phase2_activated and 
    #         conversation_state.get("current_state") == "complete" and 
    #         check_for_ml_output()):
            
    #         self.activate_phase2_automatically()
    
    # def activate_phase2_automatically(self):
    #     """Activate Phase 2 when ML file changes"""
    #     global phase2_activated, conversation_state
        
    #     try:
    #         print("🔄 File change detected - checking Phase 2 activation...")
            
    #         # Check if conditions are met
    #         phase1_complete = conversation_state.get("current_state") == "complete"
    #         can_activate = check_for_ml_output()
            
    #         print(f"[AUTO ACTIVATION] Phase 1 complete: {phase1_complete}")
    #         print(f"[AUTO ACTIVATION] Can activate: {can_activate}")
    #         print(f"[AUTO ACTIVATION] Already activated: {phase2_activated}")
            
    #         if phase1_complete and can_activate and not phase2_activated:
    #             phase2_activated = True
    #             conversation_state["phase"] = 2
    #             mark_ml_output_processed()
                
    #             # Add automatic message to conversation history
    #             auto_message = {
    #                 "user": "[SYSTEM]",
    #                 "assistant": "🎯 Phase 2 activated automatically! ML analysis updated. You can now ask about embodied carbon, improvements, or design changes.",
    #                 "phase": 2,
    #                 "trigger": "file_change",
    #                 "timestamp": time.time()
    #             }
    #             conversation_state["conversation_history"].append(auto_message)
                
    #             # Terminal message
    #             print("=" * 60)
    #             print("🎯 PHASE 2 ACTIVATED AUTOMATICALLY!")
    #             print("   Triggered by ML file change")
    #             print("   User can now ask about:")
    #             print("   • Embodied carbon analysis")
    #             print("   • Design improvements") 
    #             print("   • Material changes")
    #             print("=" * 60)
    #         else:
    #             print("❌ Phase 2 activation conditions not met")
            
    #     except Exception as e:
    #         print(f"❌ Error activating Phase 2: {e}")

#UPDATED 06.06.25
# File watcher for automatic Phase 2 activation
class MLFileWatcher(FileSystemEventHandler):
    def __init__(self):
        self.last_modified = {}
    
    def on_modified(self, event):
        if event.is_directory:
            return
            
        file_name = Path(event.src_path).name
        
        # Monitor both ML output AND input files
        if file_name not in ["ml_output.json", "compiled_ml_data.json"]:
            return
            
        current_time = time.time()
        if file_name in self.last_modified:
            if current_time - self.last_modified[file_name] < 2:  # 2 second debounce
                return
                
        self.last_modified[file_name] = current_time
        
        print(f"🔄 File watcher detected change in {file_name}")
        
        # Handle compiled_ml_data.json changes (geometry detection)
        if file_name == "compiled_ml_data.json":
            print("🔁 Detected new compiled_ml_data.json — launching ML predictor...")
            try:
                predictor_path = os.path.join(os.path.dirname(__file__), "..", "utils", "ML_predictor.py")
                subprocess.Popen(["python", predictor_path])
                print("🚀 ML_predictor.py launched successfully")
            except Exception as e:
                print(f"❌ Failed to launch ML_predictor.py: {e}")

        
        # Handle ml_output.json changes (Phase 2 activation) 
        elif file_name == "ml_output.json":
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

    
    # def check_geometry_and_trigger_phase1_completion(self):
    #     """Check for geometry and trigger Phase 1 completion if found"""
    #     global conversation_state
        
    #     try:
    #         print("🔍 [GEOMETRY WATCHER] Checking for geometry data...")
            
    #         if LLM_AVAILABLE:
    #             geometry_available = llm_calls.check_geometry_available()
    #             print(f"🔍 [GEOMETRY WATCHER] Geometry available: {geometry_available}")
                
    #             if geometry_available and conversation_state.get("current_state") != "complete":
    #                 print("🎯 [GEOMETRY WATCHER] Triggering Phase 1 completion!")
                    
    #                 # Update conversation state
    #                 conversation_state["current_state"] = "complete"
    #                 conversation_state["phase"] = 1
                    
    #                 # Trigger ML predictor
    #                 try:
    #                     predictor_path = os.path.join(os.path.dirname(__file__), "..", "utils", "ML_predictor.py")
    #                     subprocess.Popen(["python", predictor_path])
    #                     print("🚀 ML_predictor.py launched after geometry detection via file watcher")
    #                 except Exception as e:
    #                     print(f"❌ Failed to launch ML_predictor.py: {e}")
                        
    #     except Exception as e:
    #         print(f"❌ [GEOMETRY WATCHER] Error: {e}")

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
    """Hybrid intent classification: use rules first, fallback to LLM if needed."""
    input_lower = user_input.lower()

    # Step 1: Fast rule-based matches
    if any(word in input_lower for word in ["gwp", "carbon", "embodied", "emissions"]):
        return "carbon_query"
    if any(word in input_lower for word in ["optimize", "reduce", "improve", "suggest"]):
        return "improvement_suggestion"
    if any(word in input_lower for word in ["switch", "change", "update", "replace", "use"]):
        return "design_change"
    if any(word in input_lower for word in ["versions", "compare", "history", "gwp history", "best version"]):
        return "version_query"

    # Step 2: Fallback to LLM if unclear
    try:
        intent_prompt = f"""
You are an intent classifier for an architectural design assistant.

Classify the following user message into one of:
- carbon_query
- improvement_suggestion
- design_change
- general_query

Message: "{user_input}"
Only return the label.
"""
        from llm_calls import client, completion_model
        response = client.chat.completions.create(
            model=completion_model,
            messages=[{"role": "system", "content": intent_prompt}]
        )
        label = response.choices[0].message.content.strip().lower()
        if label in ["carbon_query", "improvement_suggestion", "design_change", "general_query"]:
            return label
        return "general_query"

    except Exception as e:
        print(f"[INTENT HYBRID ERROR] {e}")
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
            
                # Log to terminal only
            print("🎯 Phase 2 activated silently - processing user's question...")
        
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
                elif intent == "version_query":
                    versions = re.findall(r"\bv\d+\b", user_input.lower())
                    if len(versions) >= 2:
                        response = llm_calls.compare_versions_summary(user_input)
                    elif len(versions) == 1:
                        version_name = versions[0].upper()
                        material_keywords = ["material", "materials", "partition", "insulation", "wall", "roof", "slab"]
                        
                        if any(word in user_input.lower() for word in material_keywords):
                            response = llm_calls.summarize_version_materials(version_name)
                        else:
                            response = llm_calls.load_version_details_summary(version_name)
                    elif "best" in user_input.lower():
                        response = llm_calls.get_best_version_summary()
                    else:
                        response = llm_calls.query_version_outputs()
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
       # Call enhanced conversation management with sustainability insights
        new_state, response, updated_design_data = llm_calls.enhanced_handle_change_or_question(
        user_input, design_data
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
        


            # === START RHINO RECEIVER SERVER (new) 25.05.06 ===
            try:
                predictor_path = os.path.join(os.path.dirname(__file__), "..", "utils", "ML_predictor.py")
                subprocess.Popen(["python", predictor_path])
                print("🚀 ML_predictor.py launched after Phase 1 completion")
            except Exception as e:
                print(f"❌ Failed to launch ML_predictor.py: {e}")
            # ========================================== ENDS



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
    
@app.get("/ping")
def ping():
    return {"status": "alive"}

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

#TEMPORARY TEST FUNCTION 06.06.25
@app.get("/test_geometry")
def test_geometry():
    """Debug endpoint to test geometry detection"""
    try:
        if LLM_AVAILABLE:
            geometry_available = llm_calls.check_geometry_available()
            
            # Also check raw file content
            import json
            import os
            filepath = os.path.join("knowledge", "compiled_ml_data.json")
            with open(filepath, 'r') as f:
                raw_content = f.read()
                parsed_content = json.loads(raw_content)
            
            return {
                "geometry_available": geometry_available,
                "gfa_value": parsed_content.get("gfa"),
                "av_value": parsed_content.get("av"),
                "raw_content": raw_content,
                "parsed_content": parsed_content
            }
    except Exception as e:
        return {"error": str(e)}

#NEW FUNCTION 2 07.06.25
# Replace your existing get_initial_greeting function with this enhanced version:
@app.get("/initial_greeting")
def get_initial_greeting():
    """Get dynamic greeting - GUARANTEED to work since server startup tested it"""
    
    print("=" * 60)
    print("📞 [GREETING] Endpoint called at", time.strftime("%H:%M:%S"))
    print("   Frontend is requesting greeting...")
    print("=" * 60)
    
    # Since server startup already verified LLM works, this should never fail
    try:
        print("🤖 [GREETING] Calling generate_dynamic_greeting (server startup confirmed it works)...")
        
        # Just call it directly - no need for elaborate retry logic since startup verified it works
        greeting = llm_calls.generate_dynamic_greeting()
        
        print(f"✅ [GREETING] SUCCESS! Generated: {greeting}")
        print("=" * 60)
        
        return {
            "response": greeting,
            "state": "initial",
            "design_data": {},
            "phase": 1,
            "dynamic": True,
            "timestamp": time.strftime("%H:%M:%S"),
            "source": "llm_verified_at_startup"
        }
        
    except Exception as e:
        print(f"❌ [GREETING] UNEXPECTED ERROR (this shouldn't happen): {e}")
        print("   This is weird because server startup confirmed LLM works...")
        
        import traceback
        print(f"❌ [GREETING] Full traceback: {traceback.format_exc()}")
        print("=" * 60)
        
        # Even in error case, try one more time
        try:
            print("🔄 [GREETING] One more attempt...")
            greeting = llm_calls.generate_dynamic_greeting()
            print(f"✅ [GREETING] Second attempt worked: {greeting}")
            
            return {
                "response": greeting,
                "state": "initial",
                "design_data": {},
                "phase": 1,
                "dynamic": True,
                "timestamp": time.strftime("%H:%M:%S"),
                "source": "llm_second_attempt"
            }
        except Exception as e2:
            print(f"❌ [GREETING] Second attempt also failed: {e2}")
            
            # This should NEVER happen, but if it does, return an error instead of fallback
            return {
                "response": "🔴 LLM Error - Please refresh the page (this shouldn't happen!)",
                "state": "error",
                "design_data": {},
                "phase": 1,
                "dynamic": False,
                "error": "unexpected_llm_failure",
                "timestamp": time.strftime("%H:%M:%S")
            }

# Add this debug endpoint to test the greeting directly
@app.get("/debug_greeting")
def debug_greeting():
    """Debug endpoint to test greeting generation directly"""
    
    print("🔧 [DEBUG] Testing greeting generation...")
    
    try:
        greeting = llm_calls.generate_dynamic_greeting()
        print(f"🔧 [DEBUG] Raw greeting result: {greeting}")
        
        return {
            "success": True,
            "greeting": greeting,
            "timestamp": time.strftime("%H:%M:%S"),
            "llm_available": LLM_AVAILABLE,
            "has_client": hasattr(llm_calls, 'client'),
            "client_type": str(type(llm_calls.client)) if hasattr(llm_calls, 'client') else None
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": time.strftime("%H:%M:%S"),
            "llm_available": LLM_AVAILABLE
        }

# Also add this debug endpoint to help troubleshoot
@app.get("/llm_status")
def check_llm_status():
    """Debug endpoint to check LLM status"""
    status = {
        "llm_available_flag": LLM_AVAILABLE,
        "llm_calls_imported": "llm_calls" in sys.modules,
        "timestamp": time.strftime("%H:%M:%S")
    }
    
    try:
        import llm_calls
        status["has_client"] = hasattr(llm_calls, 'client')
        status["has_greeting_function"] = hasattr(llm_calls, 'generate_dynamic_greeting')
        
        if hasattr(llm_calls, 'client'):
            status["client_type"] = str(type(llm_calls.client))
            
            # Try to generate a greeting
            if hasattr(llm_calls, 'generate_dynamic_greeting'):
                try:
                    test_greeting = llm_calls.generate_dynamic_greeting()
                    status["can_generate_greeting"] = True
                    status["test_greeting"] = test_greeting[:50] + "..." if len(test_greeting) > 50 else test_greeting
                except Exception as e:
                    status["can_generate_greeting"] = False
                    status["greeting_error"] = str(e)
            else:
                status["can_generate_greeting"] = False
                status["greeting_error"] = "Function not found"
                
    except Exception as e:
        status["import_error"] = str(e)
    
    return status


# retrieve ml_output.json for Aymeric's TABLE // clean ml_output check independant from any other // 07/06/2025
@app.get("/api/ml_output")
def get_ml_output():
    # === Serve the decoded material composition from ml_output.json ===
    try:
        file_path = os.path.join("knowledge", "ml_output.json")
        with open(file_path, "r") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)



# retrieve iterations v{i}.json for Aymeric's PLOT // 07/06/2025
@app.get("/api/gwp_data")
def get_gwp_data():
    # === Aggregate data from all V*.json files in knowledge/iterations/ ====
    folder = os.path.join("knowledge", "iterations")
    all_data = []

    try:
        for filename in sorted(os.listdir(folder)):
            if filename.startswith("V") and filename.endswith(".json"):
                path = os.path.join(folder, filename)
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["version"] = filename.replace(".json", "")  # Add version for x-axis
                    all_data.append(data)

        return JSONResponse(content=all_data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# retrieve iterations In.json & In-1.json for Aymeric's TREND // 09/06/2025
@app.get("/api/gwp_change")
def get_gwp_change():
    """
    Compare GWP between In.json (current model) and In-1.json (previous model).
    """
    iteration_dir = Path(__file__).resolve().parent.parent / "knowledge" / "iterations"
    file_current = iteration_dir / "In.json"
    file_previous = iteration_dir / "In-1.json"

    if not file_current.exists() or not file_previous.exists():
        return JSONResponse(content={
            "error": "Required GWP files not found in iterations directory.",
            "files_found": list(p.name for p in iteration_dir.glob("*.json"))
        }, status_code=404)

    try:
        with open(file_current, "r", encoding="utf-8") as f:
            current = json.load(f)
        with open(file_previous, "r", encoding="utf-8") as f:
            previous = json.load(f)

        curr_gwp = current.get("outputs", {}).get("GWP total (kg CO2e/m²a GFA)")
        prev_gwp = previous.get("outputs", {}).get("GWP total (kg CO2e/m²a GFA)")

        if curr_gwp is None or prev_gwp is None:
            return {"error": "Missing GWP value in one of the files."}

        if prev_gwp == 0:
            return {"error": "Previous GWP is zero, cannot compute change."}

        delta = curr_gwp - prev_gwp
        percent_change = round((delta / prev_gwp) * 100, 2)

        return {
            "current": curr_gwp,
            "previous": prev_gwp,
            "delta": round(delta, 2),
            "percent_change": percent_change
        }

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# REMOVE iterations v{i}.json and v{i}.png for UI // 07/06/2025
@app.post("/api/clear_iterations")
def clear_iterations(request: Request):
    folder = os.path.join("knowledge", "iterations")
    deleted_files = []

    try:
        for filename in os.listdir(folder):
            if filename.startswith("V") and (filename.endswith(".json") or filename.endswith(".png")):
                path = os.path.join(folder, filename)
                os.remove(path)
                deleted_files.append(filename)

        return JSONResponse(content={"status": "success", "deleted": deleted_files})
    except Exception as e:
        return JSONResponse(content={"status": "error", "error": str(e)}, status_code=500)




#UPDATED 07.06.25
if __name__ == "__main__":
    print("🚀 Starting Rhino Copilot Server with Full Phase 2...")
    print(f"🤖 LLM Available: {LLM_AVAILABLE}")
    print(f"📁 ML Output Exists: {os.path.exists('knowledge/ml_output.json')}")
    print(f"🔍 Watchdog Available: {WATCHDOG_AVAILABLE}")
    

    # Initialize placeholder dictionary (NEW) 06.06.25
    if LLM_AVAILABLE:
        llm_calls.initialize_placeholder_dictionary()

    # Start file watcher in background thread
    if WATCHDOG_AVAILABLE:
        def start_watcher():
            start_file_watcher()
        
        watcher_thread = threading.Thread(target=start_watcher, daemon=True)
        watcher_thread.start()
        time.sleep(1)  # Give it a moment to start


    def find_free_port(start=5000, max_tries=20):
        for port in range(start, start + max_tries):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('127.0.0.1', port)) != 0:
                    return port
        raise RuntimeError("No free port found.")

    port = 5001

    # Check if port is in use
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('127.0.0.1', port)) == 0:
            print(f"⚠️ Port {port} is in use. Trying to find a free port...")
            port = find_free_port(5001)

    print(f"🚀 Preparing to launch server on port {port}...")

    # WAIT FOR LLM TO BE FULLY READY BEFORE STARTING SERVER
    if LLM_AVAILABLE:
        print("⏳ Ensuring LLM is fully ready before starting server...")
        max_attempts = 15
        for attempt in range(max_attempts):
            try:
                print(f"🧪 Testing LLM readiness... (attempt {attempt + 1}/{max_attempts})")
                test_greeting = llm_calls.generate_dynamic_greeting()
                print(f"✅ LLM is ready! Test greeting: {test_greeting[:50]}...")
                break
            except Exception as e:
                print(f"⏳ LLM not ready yet: {e}")
                if attempt < max_attempts - 1:
                    print("   Waiting 2 seconds before retry...")
                    time.sleep(2)
                else:
                    print("❌ LLM failed to initialize after all attempts!")
                    print("   Server will start anyway, but greetings may fail")

    print("🌟 LLM initialization complete! Starting server...")

    # Start main server
    uvicorn.run(app, host="127.0.0.1", port=5001) # later replace port=free_port
    # uvicorn.run(
    #     app, 
    #     host="127.0.0.1", 
    #     port=5001,
    #     log_level="warning",  # Only warnings and errors
    #     access_log=False      # Disable HTTP request logs
    # )


    # Save active port for debugging or UI sync
    with open("knowledge/active_port.txt", "w") as f:
        f.write(str(port))

    # Compatibility server for clients expecting port 5001
    import multiprocessing

    def run_legacy_compatibility_server():
        uvicorn.run(app, host="127.0.0.1", port=5001)
        # uvicorn.run(
        #     app, 
        #     host="127.0.0.1", 
        #     port=5001,
        #     log_level="warning",  # Only warnings and errors
        #     access_log=False      # Disable HTTP request logs
        # )


    if port != 5001:
        print("🔁 Launching compatibility server on port 5001...")
        legacy_proc = multiprocessing.Process(target=run_legacy_compatibility_server, daemon=True)
        legacy_proc.start()