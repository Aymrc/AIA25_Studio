import json
import os
import sys
import subprocess
# import time
import re
import traceback
from server.config import client, completion_model

import sys
import subprocess

# NEW IMPORTS FOR VERSIONING CONSIDERATIONS 07.06.25 
from utils.version_analysis_utils import (
    # list_all_version_files, # it is already used in version_analysis_utils.py 
    # load_specific_version, # it is already used in version_analysis_utils.py 
    summarize_version_outputs,
    get_best_version,
    extract_versions_from_input,
    summarize_versions_data,
    load_version_details
)

# Try to import César's SQL dataset utility
try:
    from utils.sql_dataset import get_top_low_carbon_high_gfa
    SQL_DATASET_AVAILABLE = True
except ImportError:
    SQL_DATASET_AVAILABLE = False
    print("SQL dataset not available - running without database features")

try:
    from utils.material_mapper import MaterialMapper
except ImportError:
    class MaterialMapper:
        def map_simple_material_to_parameters(self, material):
            mappings = {
                "brick": {"ew_par": 0, "iw_par": 0},
                "concrete": {"ew_par": 1, "iw_par": 1},
                "earth": {"ew_par": 2, "iw_par": 2},
                "straw": {"ew_par": 3, "iw_par": 3},
                "timber_frame": {"ew_par": 4, "iw_par": 4, "is_par": 1, "ro_par": 1},
                "timber_mass": {"ew_par": 5, "iw_par": 5, "is_par": 2, "ro_par": 2}
            }
            return mappings.get(material, {"ew_par": 0, "iw_par": 0})

# ==========================================
# PHASE 1 FUNCTIONS (Your System)
# ==========================================

#PLACEHOLDER DEFINITION 06.06.25
def extract_all_parameters_from_input(user_input, current_state="unknown", design_data=None):
    """Placeholder - parameter extraction disabled for new organic flow"""
    return {}  # Return empty dict since we're using placeholders

#NEW LOGIC   06.06.25
def create_ml_dictionary(design_data):
    try:
        mapper = MaterialMapper()
        
        # Complete dictionary with placeholder values from the start
        ml_dict = {
            "ew_par": 1,      # Default: concrete
            "ew_ins": 2,      # Default: EPS insulation
            "iw_par": 1,      # Default: concrete
            "es_ins": 1,      # Default: XPS
            "is_par": 0,      # Default: concrete slab
            "ro_par": 0,      # Default: concrete roof
            "ro_ins": 7,      # Default: XPS roof insulation
            "wwr": 0.3,       # Default: 30% window ratio
            "av": None,       # Will come from geometry
            "gfa": None       # Will come from geometry
        }
        
        # Override with actual design data if available
        if "materiality" in design_data:
            material = design_data["materiality"]
            print(f"[ML DICT] Processing material: {material}")
            
            material_params = mapper.map_simple_material_to_parameters(material)
            ml_dict.update(material_params)
            print(f"[ML DICT] Material parameters: {material_params}")
        
        if "wwr" in design_data:
            ml_dict["wwr"] = design_data["wwr"]
            print(f"[ML DICT] WWR: {design_data['wwr']}")
        
        print(f"[ML DICT] Complete dictionary with placeholders: {ml_dict}")
        return ml_dict
        
    except Exception as e:
        print(f"[ML DICT] Error creating ML dictionary: {e}")
        return None
    
def save_ml_dictionary(ml_dict):
    try:
        knowledge_folder = "knowledge"
        os.makedirs(knowledge_folder, exist_ok=True)
        
        filepath = os.path.join(knowledge_folder, "compiled_ml_data.json")
        with open(filepath, 'w') as f:
            json.dump(ml_dict, f, indent=2)
        
        print(f"[ML DICT] Saved to {filepath}")
        return True
        
    except Exception as e:
        print(f"[ML DICT] Error saving: {e}")
        return False

def merge_design_data(existing_data, new_data):
    merged = existing_data.copy()
    
    for key, value in new_data.items():
        if key == "geometry":
            if "geometry" not in merged:
                merged["geometry"] = {}
            for geom_key, geom_value in value.items():
                merged["geometry"][geom_key] = geom_value
                print(f"[MERGE DEBUG] Updated geometry.{geom_key} = {geom_value}")
        else:
            merged[key] = value
            print(f"[MERGE DEBUG] Updated {key} = {value}")
    
    return merged

def save_ml_dictionary(ml_dict):
    try:
        knowledge_folder = "knowledge"
        os.makedirs(knowledge_folder, exist_ok=True)
        
        filepath = os.path.join(knowledge_folder, "compiled_ml_data.json")
        with open(filepath, 'w') as f:
            json.dump(ml_dict, f, indent=2)
        
        print(f"[ML DICT] Saved to {filepath}")
        return True
        
    except Exception as e:
        print(f"[ML DICT] Error saving: {e}")
        return False

def merge_design_data(existing_data, new_data):
    merged = existing_data.copy()
    
    for key, value in new_data.items():
        if key == "geometry":
            if "geometry" not in merged:
                merged["geometry"] = {}
            for geom_key, geom_value in value.items():
                merged["geometry"][geom_key] = geom_value
                print(f"[MERGE DEBUG] Updated geometry.{geom_key} = {geom_value}")
        else:
            merged[key] = value
            print(f"[MERGE DEBUG] Updated {key} = {value}")
    
    return merged
#--------------------------------------------------
#NEW DEFINITION 07.06.25 
def provide_sustainability_insight(parameter_type, new_value):
    """Generate simple sustainability insights for parameter changes"""
    try:
        response = client.chat.completions.create(
            model=completion_model,
            messages=[
                {
                    "role": "system", 
                    "content": """
                    You are a sustainability advisor. Provide a brief, conceptual insight about how a design parameter 
                    impacts sustainability. Be encouraging and educational.
                    
                    Guidelines:
                    - EXACTLY 1 sentence
                    - Focus on the general sustainability characteristics of the parameter
                    - Don't compare to other options or make relative statements
                    - Use simple, accessible language
                    - Be positive when possible
                    
                    Examples:
                    - "Timber has excellent carbon storage properties and renewable sourcing."
                    - "Higher window ratios improve natural lighting and reduce artificial lighting needs."
                    - "Earth materials provide natural thermal regulation with minimal processing energy."
                    """
                },
                {
                    "role": "user",
                    "content": f"User selected {parameter_type}: {new_value}. Give a brief sustainability insight."
                }
            ]
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"[SUSTAINABILITY INSIGHT] Error generating insight: {e}")
        return f"Great choice with {new_value}!"

#NEW DEFINITION 07.06.25 
def enhanced_handle_change_or_question(user_input, design_data):
    """Enhanced version that detects material requests and gives sustainability insights"""
    try:
        # Check if user is requesting a material change FIRST
        user_lower = user_input.lower()
        
        # Detect material keywords in user input
        material_keywords = {
            "steel": "steel",
            "timber": "timber", 
            "wood": "timber",
            "concrete": "concrete",
            "brick": "brick",
            "earth": "earth",
            "adobe": "earth", 
            "straw": "straw",
            "mass timber": "timber_mass",
            "timber frame": "timber_frame"
        }
        
        detected_material = None
        for keyword, material in material_keywords.items():
            if keyword in user_lower:
                detected_material = material
                break
        
        # Expanded detection: change requests OR material questions
        is_material_request = detected_material and (
            # Change requests
            any(word in user_lower for word in ["change", "switch", "use", "make", "set", "material"]) or
            # Questions about materials (like "timber or steel?")
            any(word in user_lower for word in ["?", "or", "which", "what", "should", "better", "choose"]) or
            # Simple material statements ("timber", "use timber", etc.)
            len(user_input.strip().split()) <= 3
        )
        
        # If material detected and it's a material-related request, return ONLY the insight
        if is_material_request:
            # Process the change through normal flow (to update data)
            state, reply, updated_data = manage_conversation_state("active", user_input, design_data)
            
            # Generate and return ONLY the sustainability insight
            insight = provide_sustainability_insight("material", detected_material)
            
            print(f"[ENHANCED RESPONSE] Material request detected - returning ONLY insight for {detected_material}")
            print(f"[ENHANCED RESPONSE] Original input: '{user_input}'")
            
            return state, insight, updated_data
        
        # If not a material request, proceed with normal conversation flow
        return manage_conversation_state("active", user_input, design_data)
        
    except Exception as e:
        print(f"Error in enhanced_handle_change_or_question: {str(e)}")
        import traceback
        traceback.print_exc()
        # Fallback to original function
        return manage_conversation_state("active", user_input, design_data)

#NEW LOGIC     07.06.25
def determine_next_missing_parameter(design_data):
    # Check if geometry data (GFA) is available
    if not check_geometry_available():
        return "waiting_geometry", "I have your design parameters ready! Create a geometry in Rhino to see predictions."
    
    return "complete", "🎉 Perfect! Geometry detected. Generating ML predictions..."

#NEW DEFINITION 06.06.25 
def check_geometry_available():
    """Check if geometry data (GFA) exists in compiled_ml_data.json"""
    try:
        knowledge_folder = "knowledge"
        filepath = os.path.join(knowledge_folder, "compiled_ml_data.json")
        
        if not os.path.exists(filepath):
            return False
            
        with open(filepath, 'r') as f:
            ml_data = json.load(f)
        
        # Check if GFA exists and is not None/0
        gfa = ml_data.get("gfa")
        return gfa is not None and gfa > 0
        
    except Exception as e:
        print(f"[GEOMETRY CHECK] Error: {e}")
        return False

#NEW DEFINITION 07.06.25     
def update_compiled_ml_data_with_changes(parameter_updates):
    """Update compiled_ml_data.json with new parameter values"""
    try:
        import os
        import json
        from collections import OrderedDict
        
        ml_data_path = os.path.join("knowledge", "compiled_ml_data.json")
        
        # Read existing data
        if os.path.exists(ml_data_path):
            with open(ml_data_path, 'r') as f:
                current_data = json.load(f)
        else:
            # Create default structure if file doesn't exist
            current_data = {
                "ew_par": 1, "ew_ins": 2, "iw_par": 1, "es_ins": 1, 
                "is_par": 0, "ro_par": 0, "ro_ins": 7, "wwr": 0.3,
                "av": None, "gfa": None
            }
        
        # Update with new parameters
        for param_key, param_value in parameter_updates.items():
            current_data[param_key] = param_value
            print(f"[ML UPDATE] {param_key}: {param_value}")
        
        # Maintain proper order
        ordered_data = OrderedDict()
        key_order = ["ew_par", "ew_ins", "iw_par", "es_ins", "is_par", "ro_par", "ro_ins", "wwr", "av", "gfa"]
        for key in key_order:
            ordered_data[key] = current_data.get(key, 0)
        
        # Write back to file
        with open(ml_data_path, 'w') as f:
            json.dump(ordered_data, f, indent=2)
        
        print(f"[ML UPDATE] Successfully updated compiled_ml_data.json")
        return True
        
    except Exception as e:
        print(f"[ML UPDATE] Error updating compiled data: {e}")
        return False
#--------------------------------------------------
def detect_change_request(user_input):
    """Detect what type of change the user is requesting"""
    user_lower = user_input.lower()
    
    # Overall material keywords
    overall_materials = {
        "timber": "timber", "wood": "timber", "timber mass": "timber_mass", 
        "mass timber": "timber_mass", "timber frame": "timber_frame",
        "concrete": "concrete", "steel": "steel", "brick": "brick", 
        "earth": "earth", "adobe": "earth", "straw": "straw"
    }
    
    # Component-specific keywords
    component_keywords = {
        # Wall components
        "wall": "wall", "exterior wall": "ew", "ext wall": "ew", "external wall": "ew",
        "interior wall": "iw", "int wall": "iw", "internal wall": "iw",
        
        # Insulation components  
        "wall insulation": "ew_ins", "exterior wall insulation": "ew_ins",
        "roof insulation": "ro_ins", "slab insulation": "es_ins",
        
        # Roof components
        "roof": "roof", "roof partition": "ro_par",
        
        # Slab components
        "slab": "slab", "floor": "slab", "slab partition": "is_par"
    }
    
    # Material types for components
    wall_materials = ["brick", "concrete", "earth", "straw", "timber_frame", "timber_mass"]
    insulation_materials = ["cellulose", "cork", "eps", "glass_wool", "mineral_wool", "wood_fiber", "xps", "expanded_glass"]
    
    # Check for overall material change
    for material_keyword, material_name in overall_materials.items():
        if material_keyword in user_lower and any(word in user_lower for word in ["change", "switch", "use", "make", "set", "material", "to"]):
            return {
                "type": "overall_material",
                "material": material_name,
                "component": None
            }
    
    # Check for component-specific changes
    for component_keyword, component_code in component_keywords.items():
        if component_keyword in user_lower:
            # Check what material they want for this component
            for material in wall_materials + insulation_materials:
                if material in user_lower or material.replace("_", " ") in user_lower:
                    return {
                        "type": "component_specific",
                        "material": material,
                        "component": component_code
                    }
    
    # Check for material questions/comparisons
    for material_keyword, material_name in overall_materials.items():
        if material_keyword in user_lower and any(word in user_lower for word in ["?", "or", "which", "what", "should", "better", "choose"]):
            return {
                "type": "material_question",
                "material": material_name,
                "component": None
            }
    
    return None

def apply_overall_material_change(material_name):
    """Apply overall material change using MaterialMapper logic"""
    try:
        mapper = MaterialMapper()
        parameters = mapper.map_simple_material_to_parameters(material_name)
        
        print(f"[OVERALL MATERIAL] Changing to {material_name}: {parameters}")
        
        # Update the compiled ML data
        success = update_compiled_ml_data_with_changes(parameters)
        
        if success:
            return f"Changed overall building material to {material_name.replace('_', ' ')}"
        else:
            return f"Updated material selection to {material_name.replace('_', ' ')}"
            
    except Exception as e:
        print(f"[OVERALL MATERIAL] Error: {e}")
        return f"Selected {material_name.replace('_', ' ')} material"

def apply_component_specific_change(component, material):
    """Apply component-specific material change"""
    try:
        mapper = MaterialMapper()
        
        # Map component codes to parameter keys
        component_mapping = {
            "ew": "ew_par",           # Exterior wall partition
            "ew_ins": "ew_ins",       # Exterior wall insulation  
            "iw": "iw_par",           # Interior wall partition
            "wall": "ew_par",         # Default wall to exterior wall
            "roof": "ro_par",         # Roof partition
            "ro_par": "ro_par",       # Roof partition
            "ro_ins": "ro_ins",       # Roof insulation
            "slab": "is_par",         # Interior slab partition
            "is_par": "is_par",       # Interior slab partition
            "es_ins": "es_ins"        # Exterior slab insulation
        }
        
        param_key = component_mapping.get(component)
        if not param_key:
            return f"Updated {component} to {material}"
        
        # Get the material value using MaterialMapper
        category = mapper.get_category_for_param(param_key)
        if category and material in mapper.material_mappings[category]:
            material_value = mapper.material_mappings[category][material]
            
            # Update only this specific parameter
            parameter_updates = {param_key: material_value}
            success = update_compiled_ml_data_with_changes(parameter_updates)
            
            component_name = param_key.replace("_", " ").title()
            print(f"[COMPONENT CHANGE] {component_name}: {material} (value: {material_value})")
            
            if success:
                return f"Changed {component_name.lower()} to {material.replace('_', ' ')}"
            else:
                return f"Updated {component_name.lower()} to {material.replace('_', ' ')}"
        else:
            return f"Selected {material.replace('_', ' ')} for {component}"
            
    except Exception as e:
        print(f"[COMPONENT CHANGE] Error: {e}")
        return f"Updated {component} to {material.replace('_', ' ')}"

def enhanced_handle_change_or_question(user_input, design_data):
    """Enhanced version handling both overall materials and individual components"""
    try:
        # Detect what type of change the user wants
        change_request = detect_change_request(user_input)
        
        if change_request:
            print(f"[ENHANCED RESPONSE] Detected change: {change_request}")
            
            # Process the change through normal flow (to maintain conversation state)
            state, reply, updated_data = manage_conversation_state("active", user_input, design_data)
            
            change_type = change_request["type"]
            material = change_request["material"]
            component = change_request["component"]
            
            if change_type == "overall_material":
                # Apply overall material change using MaterialMapper
                change_description = apply_overall_material_change(material)
                insight = provide_sustainability_insight("overall material", material.replace('_', ' '))
                response = f"{change_description}. {insight}"
                
            elif change_type == "component_specific":
                # Apply component-specific change
                change_description = apply_component_specific_change(component, material)
                insight = provide_sustainability_insight(f"{component} material", material.replace('_', ' '))
                response = f"{change_description}. {insight}"
                
            elif change_type == "material_question":
                # Answer material question without making changes
                insight = provide_sustainability_insight("material", material.replace('_', ' '))
                response = insight
            
            else:
                response = reply
            
            print(f"[ENHANCED RESPONSE] Final response: {response}")
            return state, response, updated_data
        
        # If not a material/component change, proceed with normal conversation
        return manage_conversation_state("active", user_input, design_data)
        
    except Exception as e:
        print(f"Error in enhanced_handle_change_or_question: {str(e)}")
        import traceback
        traceback.print_exc()
        # Fallback to original function
        return manage_conversation_state("active", user_input, design_data)

def manage_conversation_state(current_state, user_input, design_data):
    print(f"[CONVERSATION DEBUG] State: {current_state}, Input: '{user_input[:50]}...', Current data keys: {list(design_data.keys())}")
    
    if not user_input.strip():
        if not design_data:
            return "initial", "Hello! I'm your design assistant. What would you like to build today?", design_data
        else:
            next_state, next_question = determine_next_missing_parameter(design_data)
            return next_state, next_question, design_data
    
    extracted_params = extract_all_parameters_from_input(user_input, current_state, design_data)
    
    if extracted_params:
        design_data = merge_design_data(design_data, extracted_params)
    
    next_state, next_question = determine_next_missing_parameter(design_data)
    
    response_parts = []
    
    if extracted_params:
        acknowledgments = []
        
        if "building_type" in extracted_params:
            acknowledgments.append(f"building type: {extracted_params['building_type']}")
        
        if "geometry" in extracted_params:
            geom = extracted_params["geometry"]
            if "number_of_levels" in geom:
                acknowledgments.append(f"{geom['number_of_levels']} levels")
        
        if "materiality" in extracted_params:
            acknowledgments.append(f"{extracted_params['materiality']} material")
        
        if "climate" in extracted_params:
            acknowledgments.append(f"{extracted_params['climate']} climate")
        
        if "wwr" in extracted_params:
            acknowledgments.append(f"{int(extracted_params['wwr']*100)}% windows")
        
        if acknowledgments:
            response_parts.append(f"Got it! {', '.join(acknowledgments)}.")
    
    if next_state == "complete":
        response_parts.append("🎉 Perfect! All basic parameters collected.")
        
        ml_dict = create_ml_dictionary(design_data)
        if ml_dict:
            save_success = save_ml_dictionary(ml_dict)
            if save_success:
                response_parts.append("✅ Material parameters ready! Geometry data will be added when you create/analyze the building geometry in Rhino.")
            else:
                response_parts.append("⚠️ Parameters collected but dictionary save failed.")
        else:
            response_parts.append("⚠️ Parameters collected but dictionary creation failed.")
    else:
        response_parts.append(next_question)
    
    final_response = " ".join(response_parts)
    
    print(f"[CONVERSATION DEBUG] Final state: {next_state}, Response: {final_response}")
    
    return next_state, final_response, design_data

def handle_change_or_question(user_input, design_data):
    try:
        state, reply, updated_data = manage_conversation_state("active", user_input, design_data)
        return state, reply, updated_data
    except Exception as e:
        print(f"Error in handle_change_or_question: {str(e)}")
        return "active", "I'm having trouble with that. Could you try rephrasing?", design_data

#NEW DEFINITION 06.06.25
def initialize_placeholder_dictionary():
    """Initialize compiled_ml_data.json with placeholder values"""
    try:
        knowledge_folder = "knowledge"
        os.makedirs(knowledge_folder, exist_ok=True)
        
        filepath = os.path.join(knowledge_folder, "compiled_ml_data.json")
        
        # Don't overwrite if file already exists (whether it has geometry or not)
        if os.path.exists(filepath):
            print("[INIT] Dictionary already exists, not overwriting")
            return True
        
        # Create placeholder dictionary
        placeholder_dict = {
            "ew_par": 1,      # Concrete walls
            "ew_ins": 2,      # EPS insulation  
            "iw_par": 1,      # Concrete interior walls
            "es_ins": 1,      # XPS slab insulation
            "is_par": 0,      # Concrete slab
            "ro_par": 0,      # Concrete roof
            "ro_ins": 7,      # XPS roof insulation
            "wwr": 0.3,       # 30% windows
            "av": None,       # Pending geometry
            "gfa": None       # Pending geometry
        }
        
        with open(filepath, 'w') as f:
            json.dump(placeholder_dict, f, indent=2)
        
        print(f"[INIT] Placeholder dictionary created at {filepath}")
        return True
        
    except Exception as e:
        print(f"[INIT] Error creating placeholder dictionary: {e}")
        return False

# ==========================================
# PHASE 2 FUNCTIONS (César's System)
# ==========================================

#AUX FUNCTIONS 08.06.25

def generate_diff_summary(before: dict, after: dict):
    """Return a human-readable summary of parameter changes."""
    diff = []
    for key in before:
        if key in after and before[key] != after[key]:
            diff.append(f"{key}: {before[key]} → {after[key]}")
    return "\n".join(diff) if diff else "No parameter differences detected."


#OLD CALLS 08.06.25

def query_intro():
    """Prompt the user to ask about their design."""
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": """
                Greet the user briefly and say: 'What would you like to know about your design?'
                Do not include any reasoning, chain-of-thought, or <think> tags. Just respond plainly.
                """
            }
        ]
    )
    return response.choices[0].message.content

def answer_user_query(user_query, design_data):
    """Return a precise, factual answer using available project data."""
    
   # NEW DEFINITION FOR VERSIONING CONSIDERATIONS 07.06.25 
    mentioned_versions = extract_versions_from_input(user_query)

    if mentioned_versions:
        version_data = summarize_versions_data(mentioned_versions)
        summary_text = json.dumps(version_data, indent=2)
    else:
        version_data = summarize_version_outputs()
        summary_text = json.dumps(version_data, indent=2)


    if mentioned_versions:
        first_version = mentioned_versions[0]
        version_details = load_version_details(first_version)
        if version_details:
            design_inputs = version_details.get("inputs_decoded", {})
            design_outputs = version_details.get("outputs", {})
        else:
            design_inputs = {}
            design_outputs = {}
    else:
        try:
            with open("knowledge/ml_output.json", "r", encoding="utf-8") as f:
                ml_data = json.load(f)
                design_inputs = ml_data.get("inputs_decoded", {})
                design_outputs = ml_data.get("outputs", {})
        except Exception as e:
            print(f"[QUERY] Failed to load ml_output.json: {e}")
            design_inputs, design_outputs = {}, {}


    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": f"""
                You are a technical assistant. Use the current design data to answer user questions.

                Design Inputs:
                {json.dumps(design_inputs, indent=2)}

                Design Outputs:
                {json.dumps(design_outputs, indent=2)}

                Respond in 1–2 concise sentences. Be direct. If unsure, say so plainly.
                """
            },
            {
                "role": "user",
                "content": user_query
            }
        ]
    )

    return response.choices[0].message.content

def suggest_improvements(user_prompt, design_data):
    """Give 1–2 brief, practical suggestions based on the design data and SQL dataset insights."""
    design_data_json = json.dumps(design_data)

    version_summary = summarize_version_outputs()
    version_summary_text = json.dumps(version_summary, indent=2)

    best_version = get_best_version()
    best_version_text = json.dumps(best_version, indent=2)

    ranking_block = "\nVersion ranking by GWP (best to worst):\n"
    sorted_versions = sorted(version_summary, key=lambda x: x.get("GWP total", float('inf')))
    for v in sorted_versions:
        ranking_block += f"- {v['version']}: {v.get('GWP total', 'N/A')} kg CO2e/m²\n"

    # Step 1: Get dataset-based reference examples (if available)
    if SQL_DATASET_AVAILABLE:
        try:
            reference_examples = get_top_low_carbon_high_gfa(max_results=3)
        except Exception as e:
            print(f"Error accessing SQL dataset: {e}")
            reference_examples = []
    else:
        reference_examples = []

    if reference_examples:
        formatted_examples = "\n".join(
            [
                f"- {row.get('Typology', 'Unknown')} | "
                f"GFA: {row.get('GFA', 'N/A')} | "
                f"GWP: {row.get('GWP total/m²GFA', row.get('GWP_total_per_m2_GFA', 'N/A'))}"
                for row in reference_examples
            ]
        )
        dataset_block = f"""
Reference examples from other projects with high GFA and low carbon footprint:
{formatted_examples}
"""
    else:
        dataset_block = "\n(No dataset matches found — skipping example injection.)\n"

    # ✅ Step 2: Build the system prompt (outside of the if block!)
    system_prompt = f"""
You are a design advisor. Suggest practical improvements using this data:

Current design:
{design_data_json}

Recent version summaries:
{version_summary_text}

Best performing version:
{best_version_text}

{ranking_block}

{dataset_block}

Answer the user's prompt in 1–2 short, specific suggestions.
Be direct. No intros, no conclusions. Do not repeat the user prompt.
If helpful, compare with previous versions or point out changes.
"""

    # Step 3: Call the LLM
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    return response.choices[0].message.content


def generate_user_summary(ml_dict):
    """Turn model inputs into a readable summary"""
    material_map = {
        0: "brick", 1: "concrete", 2: "earth", 3: "straw", 4: "timber frame", 5: "mass timber"
    }
    insulation_map = {
        0: "cellulose", 1: "cork", 2: "EPS", 3: "glass wool", 4: "mineral wool",
        5: "wood fiber", 6: "XPS", 7: "XPS"  # reused for roof
    }

    try:
        summary = f"✅ Updated design with:\n"
        summary += f"• Exterior walls: {material_map.get(ml_dict['ew_par'], 'unknown')} + {insulation_map.get(ml_dict['ew_ins'], 'unknown')} insulation\n"
        summary += f"• Interior walls: {material_map.get(ml_dict['iw_par'], 'unknown')}\n"
        summary += f"• Roof: {['concrete', 'timber frame', 'mass timber'][ml_dict['ro_par']]} + {insulation_map.get(ml_dict['ro_ins'], 'unknown')} insulation\n"
        summary += f"• Slab: {['concrete', 'timber frame', 'mass timber'][ml_dict['is_par']]}\n"
        summary += f"• WWR: {int(ml_dict['wwr'] * 100)}%\n"
        summary += f"• GFA: {ml_dict['gfa']} m²\n"
        return summary
    except Exception as e:
        print(f"[SUMMARY ERROR] {e}")
        return "✅ Design updated successfully (could not summarize changes)."


#NEW VERSION OF SUGGEST_CHANGE 08.06.25
def suggest_change(user_prompt, design_data):

    # --- Prompt construction ---
    design_data_text = json.dumps(design_data)

    # Load current compiled design dictionary
    compiled_path = os.path.join("knowledge", "compiled_ml_data.json")
    with open(compiled_path, "r", encoding="utf-8") as f:
        current_parameters = json.load(f)


    system_prompt = f"""
    You are a design assistant helping update building parameters.

    The user will describe a design change (e.g., "Change exterior wall insulation to mineral wool").
    You must:

    1. Read the current parameters below.
    2. Modify ONLY the parameters explicitly mentioned by the user.
    3. Leave all other values unchanged.
    4. Output a full dictionary with exactly these 10 keys:
       - ew_par, ew_ins, iw_par, es_ins, is_par, ro_par, ro_ins, wwr, av, gfa

    Do NOT explain the changes or include any text. Respond ONLY with a plain JSON dictionary.

    ### Current Parameters:
    {json.dumps(current_parameters, indent=2)}

    ### Parameter Options:
    - ew_par / iw_par: BRICK=0, CONCRETE=1, EARTH=2, STRAW=3, TIMBER FRAME=4, TIMBER MASS=5
    - ew_ins: CELLULOSE=0, CORK=1, EPS=2, GLASS WOOL=3, MINERAL WOOL=4, WOOD FIBER=5
    - es_ins: EXPANDED GLASS=0, XPS=1
    - is_par / ro_par: CONCRETE=0, TIMBER FRAME=1, TIMBER MASS=2
    - ro_ins: CELLULOSE=0, CORK=1, EPS=2, EXPANDED GLASS=3, GLASS WOOL=4, MINERAL WOOL=5, WOOD FIBER=6, XPS=7
    - wwr: Window-to-Wall Ratio (0.0–1.0 float)
    - av, gfa: floats from geometry system
    """


    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    raw_response = response.choices[0].message.content
    print(f"[RAW LLM RESPONSE]\n{raw_response}")


    def extract_json_block(text):
        match = re.search(r'\{[\s\S]*?\}', text)
        return match.group(0).strip() if match else None

    REQUIRED_KEYS = {
        "ew_par", "ew_ins", "iw_par", "es_ins", "is_par",
        "ro_par", "ro_ins", "wwr", "av", "gfa"
    }

    def parse_and_validate_model_response(response_text, default_inputs):
        try:
            parsed = json.loads(response_text)
            if not isinstance(parsed, dict):
                raise ValueError("Parsed content is not a dictionary.")

            missing = REQUIRED_KEYS - parsed.keys()
            for key in missing:
                print(f"[VALIDATION] Missing key: {key} → filling from defaults")
                parsed[key] = default_inputs[key]

            for key in ["wwr", "av", "gfa"]:
                parsed[key] = float(parsed[key]) if not isinstance(parsed[key], float) else parsed[key]
            for key in REQUIRED_KEYS - {"wwr", "av", "gfa"}:
                parsed[key] = int(parsed[key]) if not isinstance(parsed[key], int) else parsed[key]

            return parsed

        except Exception as e:
            raise ValueError(f"Invalid model response: {e}")

    cleaned_json = extract_json_block(raw_response)
    default_inputs = {
        "ew_par": 0, "ew_ins": 0, "iw_par": 0,
        "es_ins": 1, "is_par": 0, "ro_par": 0, "ro_ins": 0,
        "wwr": 0.3, "av": 1.0, "gfa": 1000.0
    }

    try:
        validated_dict = parse_and_validate_model_response(cleaned_json, default_inputs)

        # Merge changes with current parameters
        merged_result = current_parameters.copy()
        merged_result.update(validated_dict)

        # Enforce no unexpected changes
        for key in merged_result:
            if key not in validated_dict:
                merged_result[key] = current_parameters[key]  # Keep it unchanged


        save_ml_dictionary(merged_result)
    except ValueError as e:
        print(f"❌ Error validating LLM output: {e}")
        with open("invalid_llm_output.json", "w", encoding="utf-8") as f:
            f.write(raw_response)
        return "⚠️ I couldn't generate a valid parameter set. Please try again."

    def get_last_version_data():
        folder = "knowledge/iterations"
        try:
            files = [f for f in os.listdir(folder) if re.match(r"V\d+\.json", f)]
            files.sort(key=lambda x: int(re.search(r"\d+", x).group()), reverse=True)
            if not files:
                return None
            latest_path = os.path.join(folder, files[0])
            with open(latest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[COMPARE] Failed to load previous version: {e}")
            return None

    previous_data = get_last_version_data()

    def run_ml_predictor():
        project_root = os.path.dirname(os.path.abspath(__file__))
        predictor_path = os.path.join(project_root, "utils", "ML_predictor.py")
        python_path = sys.executable
        try:
            result = subprocess.run(
                [python_path, predictor_path],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=True
            )
            print("✅ ML Predictor output:\n", result.stdout)
        except subprocess.CalledProcessError as e:
            print("❌ ML Predictor failed:\n", e.stderr)

    run_ml_predictor()

    try:
        with open("knowledge/ml_output.json", "r", encoding="utf-8") as f:
            new_data = json.load(f)
    except Exception as e:
        print(f"[COMPARE] Failed to load new output: {e}")
        return "✅ Change saved, but unable to analyze results right now."

    diff_summary = generate_diff_summary(
        current_parameters,
        merged_result
    )


    change_explanation_prompt = f"""
    You are a helpful sustainability design advisor. The user made updates to their building design.

    Below are the two versions of the design. Use this to explain what changed in a friendly, human way. Mention only what changed.

    Keep it short and clear: 2–3 sentences. Refer to building components like walls, slabs, insulation, or window ratios.

    ### BEFORE:
    {json.dumps(previous_data.get("inputs_decoded", {}), indent=2)}

    ### AFTER:
    {json.dumps(new_data.get("inputs_decoded", {}), indent=2)}
    """

    llm_response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {"role": "system", "content": change_explanation_prompt},
            {"role": "user", "content": "Explain the design update."}
        ]
    )

    interpretation = llm_response.choices[0].message.content.strip()


    return interpretation
        

#NEW CALLS 08.06.25

def query_version_outputs():
    """Return a brief summary of all version outputs"""
    try:
        versions = summarize_version_outputs()
        summary_lines = [
            f"{v['version']}: {v['outputs'].get('GWP total', 'N/A')} kg CO2e/m²"
            for v in versions
        ]
        return "📊 Project Versions:\n" + "\n".join(summary_lines)
    except Exception as e:
        return f"⚠️ Could not summarize version outputs: {e}"

def get_best_version_summary(metric="GWP total"):
    """Identify the best version based on a given metric (default: GWP total)."""
    try:
        best_version, best_value = get_best_version(metric)
        if best_version:
            return f"🏆 Best version: **{best_version}** with {metric} = {best_value} kg CO2e/m²"
        return "⚠️ No suitable version found for comparison."

    except Exception as e:
        print(f"[BEST VERSION ERROR] {e}")
        return "⚠️ Could not determine the best version."

def compare_versions_summary(user_input):
    """Compare selected versions based on inputs and outputs."""
    try:
        version_names = extract_versions_from_input(user_input)
        if not version_names or len(version_names) < 2:
            return "⚠️ Please specify at least two versions to compare (e.g., 'Compare V2 and V5')."

        data = summarize_versions_data(version_names)
        if not data:
            return "⚠️ No matching data found for the specified versions."

        response_lines = ["🔍 Version Comparison:"]
        for version, details in data.items():
            inputs = details.get("inputs_decoded", {})
            outputs = details.get("outputs", {})
            gwp = outputs.get("GWP total", "N/A")
            eui = outputs.get("Energy Intensity - EUI (kWh/m²a)", "N/A")
            oc = outputs.get("Operational Carbon (kg CO2e/m²a GFA)", "N/A")
            ec = outputs.get("Embodied Carbon A-D (kg CO2e/m²a GFA)", "N/A")

            response_lines.append(
                f"\n📦 **{version}**\n"
                f"- GWP: {gwp} kg CO2e/m²\n"
                f"- EUI: {eui}\n"
                f"- Operational: {oc}\n"
                f"- Embodied A-D: {ec}"
            )

        return "\n".join(response_lines)

    except Exception as e:
        print(f"[COMPARE VERSIONS ERROR] {e}")
        return "⚠️ Could not compare versions due to an internal error."

def load_version_details_summary(version_name):
    """Return decoded design inputs and outputs of a specific version"""
    try:
        data = load_version_details(version_name)
        if not data:
            return f"⚠️ Version {version_name} not found."
        
        decoded = json.dumps(data.get("inputs_decoded", {}), indent=2)
        outputs = json.dumps(data.get("outputs", {}), indent=2)
        return f"📦 Design {version_name}\n\nInputs:\n{decoded}\n\nOutputs:\n{outputs}"
    except Exception as e:
        return f"⚠️ Failed to load version {version_name}: {e}"

def summarize_version_materials(version_name):
    try:
        from utils.version_analysis_utils import load_version_details
        data = load_version_details(version_name)
        decoded = data.get("inputs_decoded", {})

        response = f"📦 Materials for {version_name}:\n"
        response += f"• Exterior Wall Partition: {decoded.get('Ext.Wall_Partition', 'N/A')}\n"
        response += f"• Exterior Wall Insulation: {decoded.get('Ext.Wall_Insulation', 'N/A')}\n"
        response += f"• Interior Wall Partition: {decoded.get('Int.Wall_Partition', 'N/A')}\n"
        response += f"• External Slab Insulation: {decoded.get('Ext.Slab_Insulation', 'N/A')}\n"
        response += f"• Internal Slab Partition: {decoded.get('Int.Slab_Partition', 'N/A')}\n"
        response += f"• Roof Partition: {decoded.get('Roof_Partition', 'N/A')}\n"
        response += f"• Roof Insulation: {decoded.get('Roof_Insulation', 'N/A')}\n"
        response += f"• Window-to-Wall Ratio: {decoded.get('Window-to-Wall_Ratio', 'N/A')}\n"
        response += f"• Gross Floor Area: {decoded.get('Gross-Floor-Area', 'N/A')} m²"
        return response
    except Exception as e:
        print(f"[VERSION MATERIALS] Error: {e}")
        return f"⚠️ Could not retrieve materials for {version_name}"


# ==========================================
# DYNAMIC GREETING
# ==========================================

#NEW FUNCTION 07.06.25
# Add this function to your llm_calls.py file if it doesn't exist:

def generate_dynamic_greeting():
    """Generate a varied, engaging greeting for the design assistant"""
    try:
        print("[GREETING] Starting dynamic greeting generation...")
        
        response = client.chat.completions.create(
            model=completion_model,
            messages=[
                {
                    "role": "system",
                    "content": """
                    You are a friendly architectural design assistant. Generate a brief, welcoming greeting that:
                    - Is warm and engaging
                    - Mentions sustainable design or architecture
                    - Varies each time (don't be repetitive)
                    - Is 1-2 sentences maximum
                    
                    Generate a unique, engaging greeting now.
                    """
                }
            ],
            timeout=50.0  # 30 second timeout
        )
        
        greeting = response.choices[0].message.content.strip()
        print(f"[GREETING] Generated: {greeting}")
        return greeting
        
    except Exception as e:
        print(f"[GREETING] Error: {e}")
        import traceback
        traceback.print_exc()
        raise e  # Don't return fallback, raise error instead