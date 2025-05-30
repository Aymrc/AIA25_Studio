import json
import os
import time
from server.config import client, completion_model

# Try to import utility modules (they might not exist yet)
try:
    from utils.intent_router import classify_intent
except ImportError:
    def classify_intent(user_input):
        # Simple fallback intent classification
        if any(word in user_input.lower() for word in ['material', 'brick', 'concrete', 'timber', 'window', 'wwr']):
            return "design_change"
        elif any(word in user_input.lower() for word in ['data', 'show', 'current', 'parameters']):
            return "data_query"
        else:
            return "design_change"

try:
    from utils.material_mapper import MaterialMapper
except ImportError:
    class MaterialMapper:
        def map_materials_to_parameters(self, materials):
            # Simple fallback material mapping
            return {"ew_par": 0, "wwr": 0.3}
        
        def get_material_name(self, param_type, value):
            return f"Material_{value}"

class UnifiedLLMSystem:
    def __init__(self):
        self.material_mapper = MaterialMapper()
        self.knowledge_folder = "knowledge"
        self.ensure_knowledge_folder()
        
    def ensure_knowledge_folder(self):
        """Create knowledge folder structure"""
        os.makedirs(self.knowledge_folder, exist_ok=True)
        
        # Initialize files
        files = {
            "design_parameters.json": {},
            "rhino_geometry.json": {},
            "compiled_ml_data.json": {},
            "conversation_history.json": []
        }
        
        for filename, default_content in files.items():
            filepath = os.path.join(self.knowledge_folder, filename)
            if not os.path.exists(filepath):
                with open(filepath, 'w') as f:
                    json.dump(default_content, f, indent=2)
    
    def process_user_input(self, user_input):
        """Main processing pipeline"""
        
        # Save conversation
        self.save_conversation_turn(user_input)
        
        # Classify intent
        intent = classify_intent(user_input)
        print(f"🔍 Intent: {intent}")
        
        # Route based on intent
        if intent == "design_change":
            return self.handle_material_wwr_input(user_input)
        elif intent == "data_query":
            return self.handle_data_query(user_input)
        elif intent == "suggestion":
            return "Suggestions will be available in the next phase."
        else:
            return self.handle_material_wwr_input(user_input)  # Default to material extraction
    
    def handle_material_wwr_input(self, user_input):
        """Extract materials AND window-to-wall ratio"""
        
        # Extract both materials and WWR
        extracted_data = self.extract_materials_and_wwr(user_input)
        
        if not extracted_data.get("materials") and not extracted_data.get("wwr"):
            return "I couldn't identify materials or window ratio. Try: 'brick walls with 40% windows'"
        
        # Map materials to parameters
        parameters = {}
        
        if extracted_data.get("materials"):
            material_params = self.material_mapper.map_materials_to_parameters(extracted_data["materials"])
            parameters.update(material_params)
        
        if extracted_data.get("wwr"):
            parameters["wwr"] = extracted_data["wwr"]
        
        # Save parameters
        self.save_design_parameters(parameters)
        
        # Create response
        response_parts = []
        if extracted_data.get("materials"):
            materials_list = ", ".join([f"{k}: {v}" for k, v in extracted_data["materials"].items()])
            response_parts.append(f"Materials: {materials_list}")
        
        if extracted_data.get("wwr"):
            response_parts.append(f"Window ratio: {extracted_data['wwr']*100:.0f}%")
        
        return f"✅ Saved - {' | '.join(response_parts)}"
    
    def extract_materials_and_wwr(self, user_input):
        """Enhanced extraction for materials + WWR"""
        
        system_prompt = """
        Extract building materials and window-to-wall ratio from user input.
        Return ONLY a JSON object with this structure:
        
        {
            "materials": {
                "wall_material": "brick|concrete|earth|straw|timber_frame|timber_mass",
                "wall_insulation": "cellulose|cork|eps|glass_wool|mineral_wool|wood_fiber",
                "roof_material": "concrete|timber_frame|timber_mass", 
                "roof_insulation": "cellulose|cork|eps|extruded_glas|glass_wool|mineral_wool|wood_fiber|xps",
                "slab_material": "concrete|timber_frame|timber_mass",
                "slab_insulation": "extruded_glas|xps"
            },
            "wwr": 0.3
        }
        
        For materials: Only include keys where materials are clearly specified.
        For WWR: Extract percentages like "40% windows", "30% glazing", "0.4 window ratio" → convert to decimal (0.4).
        If no WWR mentioned, omit the "wwr" key.
        Use exact material names from the lists above.
        """
        
        try:
            response = client.chat.completions.create(
                model=completion_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ]
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Extraction error: {e}")
            return {}
    
    def save_design_parameters(self, parameters):
        """Save parameters to knowledge folder"""
        filepath = os.path.join(self.knowledge_folder, "design_parameters.json")
        
        # Load existing
        try:
            with open(filepath, 'r') as f:
                existing = json.load(f)
        except:
            existing = {}
        
        # Update with timestamp
        existing.update(parameters)
        existing["last_updated"] = time.time()
        
        # Save
        with open(filepath, 'w') as f:
            json.dump(existing, f, indent=2)
        
        print(f"💾 Parameters saved: {parameters}")
    
    def save_conversation_turn(self, user_input):
        """Save conversation history"""
        filepath = os.path.join(self.knowledge_folder, "conversation_history.json")
        
        try:
            with open(filepath, 'r') as f:
                history = json.load(f)
        except:
            history = []
        
        history.append({
            "timestamp": time.time(),
            "user_input": user_input,
            "intent": classify_intent(user_input)
        })
        
        # Keep last 50 conversations
        if len(history) > 50:
            history = history[-50:]
        
        with open(filepath, 'w') as f:
            json.dump(history, f, indent=2)
    
    def handle_data_query(self, user_input):
        """Handle data queries"""
        try:
            # Load current compiled data
            compiled_path = os.path.join(self.knowledge_folder, "compiled_ml_data.json")
            with open(compiled_path, 'r') as f:
                data = json.load(f)
            
            if not data:
                return "No design data available yet. Please specify materials and window ratio first."
            
            # Simple data display
            summary = []
            if "ew_par" in data:
                summary.append(f"Wall material: {self.material_mapper.get_material_name('ew_par', data['ew_par'])}")
            if "wwr" in data:
                summary.append(f"Window ratio: {data['wwr']*100:.0f}%")
            if "gfa" in data:
                summary.append(f"GFA: {data['gfa']:.1f}m²")
            if "av" in data:
                summary.append(f"Compactness: {data['av']:.3f}")
            
            return " | ".join(summary) if summary else "No parameters set yet."
            
        except Exception as e:
            return f"Error retrieving data: {str(e)}"

def handle_change_or_question(user_input, design_data):
    """Handle changes or questions in the Q&A phase"""
    try:
        # For now, use the unified system
        llm_system = UnifiedLLMSystem()
        reply = llm_system.process_user_input(user_input)
        return "complete", reply, design_data
    except Exception as e:
        print(f"Error in handle_change_or_question: {str(e)}")
        return "complete", "I'm having trouble answering that question. Could you try rephrasing it?", design_data

# Main function for compatibility with the modular server
def manage_conversation_state(current_state, user_input, design_data):
    """Main entry point for conversation management"""
    
    if not user_input.strip():
        # Return initial greeting
        return "initial", "Hello! I'm your design assistant. What would you like to build today?", {}
    
    try:
        # Use the unified LLM system
        llm_system = UnifiedLLMSystem()
        response = llm_system.process_user_input(user_input)
        
        # Return in expected format
        return "active", response, design_data
        
    except Exception as e:
        print(f"Error in manage_conversation_state: {str(e)}")
        return "error", f"Sorry, I encountered an error: {str(e)}", design_data