"""
Minimal Intent Router - Just handles your parameter collection system
No César's analysis part for now
"""

import sys
import os

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

class IntentRouter:
    """Minimal router that just handles your parameter collection system"""
    
    def __init__(self):
        self.conversation_state = {
            "current_state": "initial",
            "design_data": {},
            "conversation_history": [],
            "phase": 1  # Only Phase 1 for now
        }
        
        # Load only your parameter collection system
        self._load_parameter_llm()
    
    def _load_parameter_llm(self):
        """Load your parameter collection system"""
        try:
            import llm_calls
            self.parameter_llm = llm_calls
            self.parameter_llm_available = True
            print("✅ Parameter Collection LLM loaded")
        except ImportError as e:
            print(f"⚠️ Parameter LLM not available: {e}")
            self.parameter_llm_available = False
    
    def process_message(self, user_input):
        """Process message using your parameter collection system"""
        
        if not self.parameter_llm_available:
            return {"response": "Parameter collection system not available", "error": True}
        
        try:
            current_state = self.conversation_state["current_state"]
            design_data = self.conversation_state["design_data"]
            
            print(f"[ROUTER] Processing: '{user_input[:50]}...'")
            print(f"[ROUTER] Current state: {current_state}")
            
            # Use your existing conversation management
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
                "timestamp": self._get_timestamp()
            })
            
            # Check if ready for ML
            if new_state == "complete":
                response += "\n\n🎯 Parameters complete! Ready for ML processing."
            
            return {
                "response": response,
                "state": new_state,
                "design_data": updated_design_data,
                "phase": 1,
                "parameters_complete": new_state == "complete",
                "error": False
            }
            
        except Exception as e:
            print(f"[ROUTER] Error: {e}")
            return {"response": f"Error: {str(e)}", "error": True}
    
    def get_initial_greeting(self):
        """Get initial greeting from your LLM system"""
        if not self.parameter_llm_available:
            return {
                "response": "Hello! I'm your design assistant. What would you like to build today?",
                "state": "initial",
                "phase": 1,
                "is_initial_greeting": True
            }
        
        try:
            # Get greeting from your system
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
        """Phase change - simplified for now"""
        # For now, just acknowledge but stay in Phase 1
        return {"status": "success", "message": "Phase change noted, staying in Phase 1 for now", "phase": 1}
    
    def _get_timestamp(self):
        """Get current timestamp"""
        import datetime
        return datetime.datetime.now().isoformat()