"""
Unified Intent Router - Handles both parameter collection (Phase 1) and advanced analysis (Phase 2)
"""
import sys
import os
# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
def classify_intent(user_input):
    """César's intent classification for Phase 2"""
    lowered = user_input.lower()
    if any(kw in lowered for kw in ["change", "replace", "update", "modify", "set", "switch", "turn into"]):
        return "design_change"
    elif any(kw in lowered for kw in ["improve", "optimize", "minimize", "maximize", "reduce", "recommend", "should i", "could i", "how can i"]):
        return "suggestion"
    elif any(kw in lowered for kw in ["what", "how much", "how many", "show", "display", "list"]):
        return "data_query"
    elif lowered.strip() == "":
        return "fallback"
    else:
        return "unknown"
class IntentRouter:
    """Unified router that handles both Phase 1 and Phase 2 systems"""
    def __init__(self):
        self.conversation_state = {
            "current_state": "initial",
            "design_data": {},
            "conversation_history": [],
            "phase": 1  # Start in Phase 1
        }
        # Load both systems
        self._load_parameter_llm()  # Phase 1
        self._load_analysis_llm()   # Phase 2
    def _load_parameter_llm(self):
        """Load Phase 1 parameter collection system"""
        try:
            import llm_calls
            self.parameter_llm = llm_calls
            self.parameter_llm_available = True
            print(":marca_de_verificación_blanca: Phase 1 Parameter Collection LLM loaded")
        except ImportError as e:
            print(f":advertencia: Phase 1 Parameter LLM not available: {e}")
            self.parameter_llm_available = False
    def _load_analysis_llm(self):
        """Load Phase 2 analysis system"""
        try:
            import llm_calls  # Same module, different functions
            # Check if Phase 2 functions are available
            if hasattr(llm_calls, 'query_intro') and hasattr(llm_calls, 'suggest_improvements'):
                self.analysis_llm = llm_calls
                self.analysis_llm_available = True
                print(":marca_de_verificación_blanca: Phase 2 Analysis LLM loaded")
            else:
                self.analysis_llm_available = False
                print(":advertencia: Phase 2 Analysis functions not found")
        except ImportError as e:
            print(f":advertencia: Phase 2 Analysis LLM not available: {e}")
            self.analysis_llm_available = False
    def determine_phase(self):
        """Determine which phase we should be in based on current state"""
        current_state = self.conversation_state["current_state"]
        design_data = self.conversation_state["design_data"]
        # Phase 1: Parameter collection (incomplete data)
        if current_state in ["initial", "materiality", "climate", "wwr"]:
            return 1
        # Phase 2: Analysis and optimization (complete data)
        if current_state == "complete" or self._has_sufficient_data(design_data):
            return 2
        # Default to Phase 1
        return 1
    def _has_sufficient_data(self, design_data):
        """Check if we have enough data for Phase 2 analysis"""
        required_fields = ["materiality", "climate", "wwr"]
        return all(field in design_data for field in required_fields)
    def process_message(self, user_input):
        """Process message using appropriate phase system"""
        # Determine current phase
        current_phase = self.determine_phase()
        # Update phase if it changed
        if current_phase != self.conversation_state["phase"]:
            self.conversation_state["phase"] = current_phase
            print(f"[ROUTER] Switched to Phase {current_phase}")
        # Route to appropriate system
        if current_phase == 1:
            return self._process_phase1(user_input)
        elif current_phase == 2:
            return self._process_phase2(user_input)
        else:
            return {"response": "System error: unknown phase", "error": True}
    def _process_phase1(self, user_input):
        """Process Phase 1 - Parameter Collection"""
        if not self.parameter_llm_available:
            return {"response": "Parameter collection system not available", "error": True}
        try:
            current_state = self.conversation_state["current_state"]
            design_data = self.conversation_state["design_data"]
            print(f"[ROUTER PHASE 1] Processing: '{user_input[:50]}...'")
            print(f"[ROUTER PHASE 1] Current state: {current_state}")
            # Use Phase 1 conversation management
            new_state, response, updated_design_data = self.parameter_llm.manage_conversation_state(
                current_state, user_input, design_data
            )
            # Update state
            self.conversation_state["current_state"] = new_state
            self.conversation_state["design_data"] = updated_design_data
            # Add to history
            self.conversation_state["conversation_history"].append({
                "user": user_input,
                "assistant": response,
                "state": new_state,
                "phase": 1,
                "timestamp": self._get_timestamp()
            })
            # Check if ready for Phase 2
            if new_state == "complete":
                response += "\n\n:dardo: Phase 1 complete! You can now ask for design analysis, improvements, or changes."
                self.conversation_state["phase"] = 2
            return {
                "response": response,
                "state": new_state,
                "design_data": updated_design_data,
                "phase": self.conversation_state["phase"],
                "parameters_complete": new_state == "complete",
                "error": False
            }
        except Exception as e:
            print(f"[ROUTER PHASE 1] Error: {e}")
            return {"response": f"Phase 1 Error: {str(e)}", "error": True}
    def _process_phase2(self, user_input):
        """Process Phase 2 - Analysis and Optimization"""
        if not self.analysis_llm_available:
            return {
                "response": "Analysis system not available. You can still modify parameters by describing changes.",
                "error": False,
                "phase": 2
            }
        try:
            design_data = self.conversation_state["design_data"]
            intent = classify_intent(user_input)
            print(f"[ROUTER PHASE 2] Processing: '{user_input[:50]}...'")
            print(f"[ROUTER PHASE 2] Intent: {intent}")
            # Route based on intent
            if intent == "data_query":
                response = self.analysis_llm.answer_user_query(user_input, design_data)
            elif intent == "suggestion":
                response = self.analysis_llm.suggest_improvements(user_input, design_data)
            elif intent == "design_change":
                response = self.analysis_llm.suggest_change(user_input, design_data)
            elif intent == "fallback":
                response = self.analysis_llm.query_intro()
            else:
                response = "I can help you analyze your design, suggest improvements, or make changes. What would you like to know?"
            # Add to history
            self.conversation_state["conversation_history"].append({
                "user": user_input,
                "assistant": response,
                "intent": intent,
                "phase": 2,
                "timestamp": self._get_timestamp()
            })
            return {
                "response": response,
                "state": "analysis",
                "design_data": design_data,
                "phase": 2,
                "intent": intent,
                "parameters_complete": True,
                "error": False
            }
        except Exception as e:
            print(f"[ROUTER PHASE 2] Error: {e}")
            return {"response": f"Phase 2 Error: {str(e)}", "error": True}
    def get_initial_greeting(self):
        """Get initial greeting - always starts in Phase 1"""
        if not self.parameter_llm_available:
            return {
                "response": "Hello! I'm your design assistant. What would you like to build today?",
                "state": "initial",
                "phase": 1,
                "is_initial_greeting": True
            }
        try:
            # Get greeting from Phase 1 system
            initial_state, greeting, initial_data = self.parameter_llm.manage_conversation_state(
                "initial", "", {}
            )
            return {
                "response": greeting,
                "state": initial_state,
                "design_data": initial_data,
                "phase": 1,
                "is_initial_greeting": True
            }
        except Exception as e:
            print(f"[ROUTER] Error getting greeting: {e}")
            return {
                "response": "Hello! I'm your design assistant. What would you like to build today?",
                "state": "initial",
                "phase": 1,
                "is_initial_greeting": True
            }
    def get_conversation_state(self):
        """Get current conversation state"""
        return {
            "state": self.conversation_state["current_state"],
            "design_data": self.conversation_state["design_data"],
            "phase": self.conversation_state["phase"],
            "parameters_complete": self.conversation_state["current_state"] == "complete",
            "conversation_history": self.conversation_state["conversation_history"][-5:]
        }
    def get_design_parameters(self):
        """Get formatted design parameters"""
        try:
            design_data = self.conversation_state["design_data"]
            formatted_data = {
                "building_type": design_data.get("building_type", "Not specified"),
                "geometry": design_data.get("geometry", {}),
                "materiality": design_data.get("materiality", "Not specified"),
                "climate": design_data.get("climate", "Not specified"),
                "wwr": design_data.get("wwr", "Not specified"),
                "self_modeling": design_data.get("self_modeling", True),
                "completion_status": self.conversation_state["current_state"],
                "phase": self.conversation_state["phase"]
            }
            return {"status": "success", "data": formatted_data}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    def change_phase(self, new_phase, ml_results=None):
        """Manual phase change"""
        if new_phase in [1, 2]:
            old_phase = self.conversation_state["phase"]
            self.conversation_state["phase"] = new_phase
            message = f"Switched from Phase {old_phase} to Phase {new_phase}"
            if new_phase == 2 and ml_results:
                message += " with ML results integrated"
            return {"status": "success", "message": message, "phase": new_phase}
        else:
            return {"status": "error", "message": "Invalid phase", "phase": self.conversation_state["phase"]}
    def _get_timestamp(self):
        """Get current timestamp"""
        import datetime
        return datetime.datetime.now().isoformat()