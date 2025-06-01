import json
import os
# import time
import re
import traceback
from server.config import client, completion_model

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

def extract_all_parameters_from_input(user_input, current_state="unknown", design_data=None):
    try:
        extracted = {}
        input_lower = user_input.lower().strip()
        
        if not input_lower:
            return extracted
            
        design_data = design_data or {}
        
        print(f"[EXTRACTION DEBUG] Input: '{user_input}'")
        print(f"[EXTRACTION DEBUG] Current state: {current_state}")
        
        # Only use context-aware single-word extraction for simple inputs
        if current_state == "wwr" and re.match(r'^\s*\d+\s*(?:percent|%)?\s*$', input_lower):
            wwr_match = re.search(r'(\d+)', input_lower)
            if wwr_match:
                percentage = float(wwr_match.group(1))
                if percentage > 1:
                    percentage = percentage / 100
                extracted["wwr"] = round(min(percentage, 0.9), 2)
                print(f"[EXTRACTION DEBUG] Context-aware WWR: {extracted['wwr']}")
                return extracted
        
        # Level patterns
        level_patterns = [
            r'(\d+)\s*(?:storey|story|stories|level|floor)s?(?:\s+(?:building|structure))?',
            r'(\d+)\s*levels?',
            r'(\d+)[-\s]*level',
            r'(\d+)[-\s]*storey',
            r'(\d+)\s*floors?',
            r'(?:building\s+with\s+)?(\d+)\s+(?:level|floor|storey)',
            r'(\d+)[-\s]*story(?:\s+building)?'
        ]
        for pattern in level_patterns:
            match = re.search(pattern, input_lower)
            if match:
                levels = min(int(match.group(1)), 10)
                if "geometry" not in extracted:
                    extracted["geometry"] = {}
                extracted["geometry"]["number_of_levels"] = levels
                print(f"[EXTRACTION DEBUG] Found levels: {levels}")
                break
        
        # Building type patterns
        building_patterns = {
            "residential": ["residential", "apartment", "housing", "house", "home", "flat", "condo"],
            "office": ["office", "commercial", "workplace", "business", "office building"],
            "hotel": ["hotel", "hospitality", "accommodation", "resort", "inn", "motel"],
            "mixed-use": ["mixed-use", "mixed use", "multi-use", "multiple use"],
            "museum": ["museum", "gallery", "cultural", "exhibition", "art museum"],
            "hospital": ["hospital", "medical", "healthcare", "clinic", "medical center"],
            "school": ["school", "educational", "university", "college", "education"],
            "retail": ["retail", "shop", "store", "shopping", "commercial retail"]
        }
        
        for building_type, patterns in building_patterns.items():
            if any(pattern in input_lower for pattern in patterns):
                extracted["building_type"] = building_type
                print(f"[EXTRACTION DEBUG] Found building type: {building_type}")
                break
        
        # Material patterns
        material_patterns = {
            "brick": ["brick", "masonry", "brick walls", "bricks", "clay brick", "red brick"],
            "concrete": ["concrete", "cement", "concrete walls", "reinforced concrete"],
            "earth": ["earth", "adobe", "mud", "earthen", "clay", "rammed earth", "cob"],
            "straw": ["straw", "straw bale", "hay", "strawbale", "straw walls"],
            "timber_frame": ["timber frame", "wood frame", "wooden frame", "frame construction"],
            "timber_mass": ["timber mass", "mass timber", "timber", "wood", "wooden", "solid timber", "heavy timber", "logs"]
        }
        
        for material, patterns in material_patterns.items():
            if any(pattern in input_lower for pattern in patterns):
                extracted["materiality"] = material
                print(f"[EXTRACTION DEBUG] Found material: {material}")
                break
        
        # Climate patterns
        climate_patterns = {
            "cold": ["cold", "winter", "freezing", "snow", "cold climate"],
            "hot-humid": ["hot humid", "hot", "tropical", "humid", "summer", "hot climate"],
            "arid": ["arid", "dry", "desert", "arid climate", "dry climate"],
            "temperate": ["temperate", "mild", "moderate", "temperate climate"]
        }
        
        for climate, patterns in climate_patterns.items():
            if any(pattern in input_lower for pattern in patterns):
                extracted["climate"] = climate
                print(f"[EXTRACTION DEBUG] Found climate: {climate}")
                break
        
        # WWR patterns
        wwr_patterns = [
            r'wwr:\s*(\d+)',
            r'(\d+)%?\s*(?:window|glazing|glass|windows)',
            r'(?:window|wwr|glazing).*?(\d+)%?',
            r'(\d+)%?\s*wwr',
            r'(\d+)\s*percent\s*(?:window|glass|glazing)',
            r'^\s*(\d+)\s*$',
            r'^\s*(\d+)\s*percent\s*$',
            r'^\s*(\d+)%\s*$',
            r'^\s*0\.(\d+)\s*$',
            r'(\d+)\s*percent'
        ]
        
        for pattern in wwr_patterns:
            match = re.search(pattern, input_lower)
            if match:
                percentage = float(match.group(1))
                
                if pattern == r'^\s*0\.(\d+)\s*$':
                    percentage = float(f"0.{match.group(1)}") * 100
                
                if percentage > 1:
                    percentage = percentage / 100
                    
                extracted["wwr"] = round(min(percentage, 0.9), 2)
                print(f"[EXTRACTION DEBUG] Found WWR: {extracted['wwr']}")
                break
        
        print(f"[EXTRACTION DEBUG] Final extracted: {extracted}")
        return extracted
        
    except Exception as e:
        print(f"Error in parameter extraction: {str(e)}")
        traceback.print_exc()
        return {}

def create_ml_dictionary(design_data):
    try:
        mapper = MaterialMapper()
        
        ml_dict = {
            "ew_par": 0,
            "ew_ins": 0,
            "iw_par": 0,
            "es_ins": 1,
            "is_par": 0,
            "ro_par": 0,
            "ro_ins": 0,
            "wwr": 0.3
        }
        
        if "materiality" in design_data:
            material = design_data["materiality"]
            print(f"[ML DICT] Processing material: {material}")
            
            material_params = mapper.map_simple_material_to_parameters(material)
            ml_dict.update(material_params)
            print(f"[ML DICT] Material parameters: {material_params}")
        
        if "wwr" in design_data:
            ml_dict["wwr"] = design_data["wwr"]
            print(f"[ML DICT] WWR: {design_data['wwr']}")
        
        print(f"[ML DICT] Partial dictionary (geometry data pending): {ml_dict}")
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

def determine_next_missing_parameter(design_data):
    if "materiality" not in design_data:
        return "materiality", "What material would you like to use? (brick, concrete, timber, earth, straw)"
        
    if "climate" not in design_data:
        return "climate", "What climate will this building be in? (cold, hot-humid, arid, temperate)"
        
    if "wwr" not in design_data:
        return "wwr", "What percentage of windows would you like? (e.g., 30%, 40%)"
    
    return "complete", "🎉 Perfect! All basic parameters collected. Generating ML dictionary..."

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

# ==========================================
# PHASE 2 FUNCTIONS (César's System)
# ==========================================

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
    design_data_json = json.dumps(design_data)
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": f"""
                You are a technical assistant. Answer the user's question using only this data:

                {design_data_json}

                Respond in 1–2 concise sentences. If the answer isn't in the data, say so directly.
                Avoid unnecessary explanations.
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

    # Step 2: Build the system prompt
    system_prompt = f"""
You are a design advisor. Suggest practical improvements using this data:

Current design:
{design_data_json}
{dataset_block}

Answer the user's prompt in 1–2 short, specific suggestions.
Be direct. No intros, no conclusions. Do not repeat the user prompt.
Only suggest changes relevant to this design.
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

def suggest_change(user_prompt, design_data):
    

    """Interpret user's design change request and return a structured parameter dictionary."""
    design_data_text = json.dumps(design_data)

    system_prompt = f"""
        You are a design assistant. The user will request a design change. You must respond ONLY with a JSON object that represents a complete parameter configuration.

        ### Output format (mandatory structure):
        {{
            "ew_par": 0,
            "ew_ins": 0,
            "iw_par": 0,
            "es_ins": 1,
            "is_par": 0,
            "ro_par": 0,
            "ro_ins": 0,
            "wwr": 0.3,
        }}

        ### Parameter definitions:
        - ew_par: Exterior Wall Partitions → BRICK=0, CONCRETE=1, EARTH=2, STRAW=3, TIMBER FRAME=4, TIMBER MASS=5  
        - ew_ins: Exterior Wall Insulation → CELLULOSE=0, CORK=1, EPS=2, GLASS WOOL=3, MINERAL WOOL=4, WOOD FIBER=5  
        - iw_par: Interior Wall Partitions → same as ew_par  
        - es_ins: Exterior Slabs Insulation → EXPANDED GLASS=0, XPS=1  
        - is_par: Interior Slabs → CONCRETE=0, TIMBER FRAME=1, TIMBER MASS=2  
        - ro_par: Roof Slabs → CONCRETE=0, TIMBER FRAME=1, TIMBER MASS=2  
        - ro_ins: Roof Insulation → CELLULOSE=0, CORK=1, EPS=2, EXPANDED GLASS=3, GLASS WOOL=4, MINERAL WOOL=5, WOOD FIBER=6, XPS=7  
        - wwr: Window-to-Wall Ratio → float (0.0–1.0)  
        - gfa: Gross Floor Area → float (no units)  
        - av: Air Volume → float

        ### Language alias mapping:
        - "wood" → TIMBER MASS (5)  
        - "wood frame" → TIMBER FRAME (4)  
        - "concrete" → CONCRETE (1)  
        - "brick" → BRICK (0)  
        - "earth" → EARTH (2)  
        - "straw" → STRAW (3)

        ### Output rules:
        - Respond with the full dictionary, even if the user only changes one thing.
        - Format gfa, wwr, av as floats (e.g., 4800.0). Do not return strings or include units.
        - No explanations. No extra text. Only JSON.

        Use this project data if relevant:
        {design_data_text}
        """

    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    banana=response.choices[0].message.content
    
    # --- Overwrite ML input ---
    
    save_ml_dictionary(banana)

    # --- Trigger ML_predictor.py ---
    import subprocess
    import os
    import sys
    def run_ml_predictor():
        project_root = os.path.dirname(os.path.abspath(__file__))
        predictor_path = os.path.join(project_root, "utils", "ML_predictor.py")
        python_path = sys.executable  # Current Python interpreter
        try:
            result = subprocess.run(
                [python_path, predictor_path],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=True
            )
            print(":marca_de_verificación_blanca: ML Predictor output:\n", result.stdout)
        except subprocess.CalledProcessError as e:
            print(":x: ML Predictor failed:")
            print(e.stderr)
    # Call it
    run_ml_predictor()


    return response.choices[0].message.content
















