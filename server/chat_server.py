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
from utils.embeddings import classify_intent_via_embeddings

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
 
# Global conversation state
conversation_state = {
    "design_data": {},
    "conversation_history": [],
}

# File system observer for ML file changes
file_observer = None

# Watches ML-related files and runs ML_predictor.py if compiled_ml_data.json changes.
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

#start_file_watcher(): Initializes and starts the file-watching service if possible.       
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

#ChatRequest: Data model for receiving chat messages via POST.
class ChatRequest(BaseModel):
    message: str


# export report endpoint
@app.post("/api/export_report")
def export_report():
    try:
        result = subprocess.run(
            ["python", "utils/export.py"],
            capture_output=True,
            text=True,
            check=True
        )
        return {"status": "success", "message": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": e.stderr}

# chat_endpoint(): Main chat handler that routes user input to the appropriate LLM function using ML data.
# @app.post("/chat")
# def chat_endpoint(req: ChatRequest):
#     """Handle user input using ML-enhanced analysis"""
#     global conversation_state

#     if not LLM_AVAILABLE:
#         return {"response": "LLM system not available - check imports"}

#     try:
#         user_input = req.message.strip()

#         print(f"[CHAT] Input: '{user_input}'")
#         print(f"[CHAT] Handling input as ML-enhanced request")
#         print(f"[CHAT] ML file exists: {os.path.exists('knowledge/ml_output.json')}")

#         # --- Core ML-based Chat Handling ---
#         print("🔍 Starting ML analysis pipeline...")

#         # Classify intent
#         from utils.embeddings import classify_intent_via_embeddings

#         intent, score = classify_intent_via_embeddings(user_input)
#         print(f"[🔎 EMBEDDING INTENT] → {intent} (score={score:.4f})")

#         # Get current design data
#         design_data = conversation_state.get("design_data", {})
#         print(f"🔍 Design data keys: {list(design_data.keys())}")

#         # Load ML output
#         ml_data = {}
#         ml_file = "knowledge/ml_output.json"

#         print(f"🔍 Checking ML file: {ml_file}")
#         if os.path.exists(ml_file):
#             try:
#                 with open(ml_file, 'r') as f:
#                     ml_data = json.load(f)

#                 print(f"✅ ML data loaded with keys: {list(ml_data.keys())}")
#                 if 'carbon' in ml_data:
#                     print(f"✅ Carbon data found")
#                 if 'energy' in ml_data:
#                     print(f"✅ Energy data found")

#             except Exception as e:
#                 print(f"❌ Error reading ML file: {e}")
#                 return {
#                     "response": f"❌ Error reading ML analysis file: {str(e)}",
#                     "mode": "ml_analysis",
#                     "error": True
#                 }
#         else:
#             print("❌ ML output file does not exist!")
#             return {
#                 "response": "❌ No ML analysis data found. Please ensure the ML analysis has completed and ml_output.json exists.",
#                 "mode": "ml_analysis",
#                 "error": True
#             }

#         # Build data package
#         comprehensive_data = {
#             "building_parameters": design_data,
#             "carbon_analysis": ml_data.get('carbon', {}),
#             "energy_analysis": ml_data.get('energy', {}),
#             "ml_results": ml_data,
#             "analysis_complete": True,
#             "data_source": "ml_output.json"
#         }

#         print(f"✅ Data package ready")

#         # Route based on intent
#         # if intent == "carbon_query":
#         #     response = llm_calls.answer_user_query(user_input, comprehensive_data)
#         # elif intent == "improvement_suggestion":
#         #     response = llm_calls.suggest_improvements(user_input, comprehensive_data)
#         # elif intent == "design_change":
#         #     response = llm_calls.suggest_change(user_input, comprehensive_data)
#         # elif intent == "version_query":
#         #     versions = re.findall(r"\bv\d+\b", user_input.lower())

#         #     if len(versions) >= 2:
#         #         response = llm_calls.compare_versions_summary(user_input)

#         #     elif len(versions) == 1:
#         #         version_name = versions[0].upper()
#         #         material_keywords = ["material", "materials", "partition", "insulation", "wall", "roof", "slab"]
#         #         if any(word in user_input.lower() for word in material_keywords):
#         #             response = llm_calls.summarize_version_materials(version_name)
#         #         else:
#         #             response = llm_calls.load_version_details_summary(version_name)

#         #     else:
#         #         # Subintent detection via embeddings
#         #         subintent_examples = {
#         #             "list_versions": [
#         #                 "list all versions",
#         #                 "show saved iterations",
#         #                 "version history",
#         #                 "show project versions",
#         #                 "summarize saved versions",
#         #                 "which designs do we have"
#         #             ],
#         #             "best_version": [
#         #                 "which version is most sustainable",
#         #                 "what design performs best",
#         #                 "lowest GWP",
#         #                 "best performing design",
#         #                 "most efficient iteration",
#         #                 "top sustainability version",
#         #                 "preferred version",
#         #                 "lowest carbon footprint version",
#         #                 "which version is the greenest"
#         #             ],
#         #             "version_summary": [
#         #                 "what are the saved versions",
#         #                 "summarize designs",
#         #                 "overview of versions",
#         #                 "available iterations",
#         #                 "give me a version summary"
#         #             ]
#         #         }

#         #         subintent, score = classify_intent_via_embeddings(user_input, subintent_examples)
#         #         print(f"[🔎 SUBINTENT via EMBEDDINGS] → {subintent} (score={score:.4f})")

#         #         if subintent == "best_version":
#         #             response = llm_calls.get_best_version_summary()
#         #         elif subintent in ["list_versions", "version_summary"]:
#         #             response = llm_calls.query_version_outputs()
#         #         else:
#         #             # fallback
#         #             response = llm_calls.query_version_outputs()
       
#         # else:
#         #     response = llm_calls.answer_user_query(user_input, comprehensive_data)

#         from utils.copilot_graph import build_copilot_graph, CopilotState

#         copilot_graph = build_copilot_graph()

#         initial_state = CopilotState(
#             user_input=user_input,
#             design_data=comprehensive_data
#         )

#         final_state = copilot_graph.invoke(initial_state)

#         response = final_state.llm_response
#         intent = final_state.intent


#         final_state = copilot_graph.invoke(initial_state)
#         print("🧠 LangGraph resultado:", final_state)


#         print(f"✅ LLM response received")

#         # Save to conversation history
#         conversation_state["conversation_history"].append({
#             "user": user_input,
#             "assistant": response,
#             "mode": "ml_analysis",
#             "intent": intent,
#             "timestamp": time.time()
#         })

#         return {
#             "response": response,
#             "mode": "ml_analysis",
#             "state": "analysis",
#             "intent": intent,
#             "design_data": comprehensive_data,
#             "error": False
#         }

#     except Exception as e:
#         print(f"[CHAT] Unexpected error: {e}")
#         import traceback
#         traceback.print_exc()
#         return {
#             "response": f"❌ Unexpected server error: {str(e)}",
#             "mode": "ml_analysis",
#             "error": True
#         }

from utils.copilot_graph import CopilotState, build_copilot_graph

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    user_input = req.message.strip()
    design_data = conversation_state.get("design_data", {})
    
    # Crear estado inicial
    state = CopilotState(user_input=user_input, design_data=design_data)
    
    # Ejecutar el grafo
    graph = build_copilot_graph()
    result = graph.invoke(state)

    # Empaquetar la respuesta
    response = {
        "response": result["llm_response"],
        "intent": result["intent"],
        "mode": "langgraph",
        "error": False
    }

    # 👇 Esto imprime el JSON resultante en la consola
    print(f"\n📤 Chat Response JSON:\n{json.dumps(response, indent=4)}\n")

    conversation_state["conversation_history"].append({
        "user": user_input,
        "assistant": result["llm_response"],
        "mode": "langgraph",
        "intent": result["intent"],
        "timestamp": time.time()
    })

    return response

#ping(): Health check endpoint that returns "alive".
@app.get("/ping")
def ping():
    return {"status": "alive"}

#get_conversation_state(): Returns the most recent 5 chat interactions and whether ML file/watcher is active.
@app.get("/conversation_state")
def get_conversation_state():
    """Get current conversation state"""
    return {
    "design_data": conversation_state.get("design_data", {}),
    "ml_output_exists": os.path.exists("knowledge/ml_output.json"),
    "file_watcher_active": file_observer is not None and file_observer.is_alive() if WATCHDOG_AVAILABLE else False,
    "conversation_history": conversation_state["conversation_history"][-5:]
}

#debug_analysis_data(): Returns a deep view of the design + ML data sent to LLMs.
@app.post("/debug_analysis_data")
def debug_analysis_data():
    """Debug endpoint to inspect the ML-enhanced analysis data package"""
    try:
        design_data = conversation_state.get("design_data", {})
        ml_data = {}

        ml_file = "knowledge/ml_output.json"
        if os.path.exists(ml_file):
            with open(ml_file, 'r') as f:
                ml_data = json.load(f)

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

#health_check(): Returns general server health and LLM readiness.
@app.get("/")
def health_check():
    return {
        "status": "ok", 
        "message": "Rhino Copilot Server with Full Phase 2", 
        "llm_available": LLM_AVAILABLE,
        "mode": "ml_analysis",
        "ml_output_exists": os.path.exists("knowledge/ml_output.json"),
        "watchdog_available": WATCHDOG_AVAILABLE
    }

#test_geometry(): Verifies if compiled_ml_data.json contains valid geometry info.
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

#get_initial_greeting(): Generates and returns a startup greeting via the LLM.
@app.get("/initial_greeting")
def get_initial_greeting():
    """Return a dynamic greeting verified at startup (LLM-based)"""

    print("=" * 60)
    print("📞 [GREETING] Endpoint called at", time.strftime("%H:%M:%S"))
    print("   Frontend is requesting greeting...")
    print("=" * 60)

    try:
        print("🤖 [GREETING] Calling generate_dynamic_greeting...")
        greeting = llm_calls.generate_dynamic_greeting()
        print(f"✅ [GREETING] SUCCESS! Generated: {greeting}")
        print("=" * 60)

        return {
            "response": greeting,
            "state": "ready",
            "design_data": {},
            "mode": "ml_analysis",
            "dynamic": True,
            "timestamp": time.strftime("%H:%M:%S"),
            "source": "llm_verified_at_startup"
        }

    except Exception as e:
        print(f"❌ [GREETING] UNEXPECTED ERROR: {e}")
        import traceback
        print(f"❌ [GREETING] Full traceback: {traceback.format_exc()}")
        print("=" * 60)

        # Retry once more
        try:
            print("🔄 [GREETING] Retrying...")
            greeting = llm_calls.generate_dynamic_greeting()
            print(f"✅ [GREETING] Retry success: {greeting}")
            return {
                "response": greeting,
                "state": "ready",
                "design_data": {},
                "mode": "ml_analysis",
                "dynamic": True,
                "timestamp": time.strftime("%H:%M:%S"),
                "source": "llm_second_attempt"
            }
        except Exception as e2:
            print(f"❌ [GREETING] Retry failed: {e2}")
            return {
                "response": "🔴 LLM Error - Please refresh the page (this shouldn't happen!)",
                "state": "error",
                "design_data": {},
                "mode": "ml_analysis",
                "dynamic": False,
                "error": "unexpected_llm_failure",
                "timestamp": time.strftime("%H:%M:%S")
            }

#debug_greeting(): Debug tool to test if LLM greeting generation works.
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

#heck_llm_status(): Full diagnostic of the LLM system's availability and behavior.
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

#get_gwp_data(): Collects all versioned GWP data files (V*.json) for Aymeric’s plot.
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

#get_gwp_change(): Compares current (In.json) and previous (In-1.json) model GWP values.
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

#clear_iterations(): Deletes all V*.json and .png iteration files for cleanup.
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

#__main__ block: Boots the LLM, starts file watching, waits for readiness, and runs the server on a free port.
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
    # uvicorn.run(app, host="127.0.0.1", port=5001) # later replace port=free_port
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=5001,
        log_level="warning",  # Only warnings and errors
        access_log=False      # Disable HTTP request logs
    )


    # Save active port for debugging or UI sync
    with open("knowledge/active_port.txt", "w") as f:
        f.write(str(port))

    # Compatibility server for clients expecting port 5001
    import multiprocessing

    def run_legacy_compatibility_server():
        # uvicorn.run(app, host="127.0.0.1", port=5001)
        uvicorn.run(
            app, 
            host="127.0.0.1", 
            port=5001,
            log_level="warning",  # Only warnings and errors
            access_log=False      # Disable HTTP request logs
        )


    if port != 5001:
        print("🔁 Launching compatibility server on port 5001...")
        legacy_proc = multiprocessing.Process(target=run_legacy_compatibility_server, daemon=True)
        legacy_proc.start()