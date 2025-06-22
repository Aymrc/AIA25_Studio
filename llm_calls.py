# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                            1. LLM Setup & Utilities                        ║
# ╚════════════════════════════════════════════════════════════════════════════╝

import json
import os
import sys
import subprocess
import re
import traceback
from server.config import client, completion_model

# -- Optional imports for external features --
try:
    from utils.sql_dataset import get_top_low_carbon_high_gfa
    SQL_DATASET_AVAILABLE = True
except ImportError:
    SQL_DATASET_AVAILABLE = False
    print("SQL dataset not available - running without database features")
try:
    from utils.material_mapper import MaterialMapper
except ImportError:
    print("Failed importing MaterialMapper")


# -- Generate dynamic LLM greeting --
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
        traceback.print_exc()
        raise e  # Don't return fallback, raise error instead

# -- Provide 1-sentence sustainability insight --
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

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                          2. Design Data Handling                           ║
# ╚════════════════════════════════════════════════════════════════════════════╝

# -- Initialize compiled ML dictionary with placeholder values --
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
            "ew_par": 1,
            "ew_ins": 2,
            "iw_par": 1,
            "es_ins": 1,
            "is_par": 0,
            "ro_par": 0,
            "ro_ins": 7,
            "wwr": 0.3,
            "A/V": 0.4,
            "Volume(m3)": 1000.0,
            "VOL/VOLBBOX": 1.0
        }

        
        with open(filepath, 'w') as f:
            json.dump(placeholder_dict, f, indent=2)
        
        print(f"[INIT] Placeholder dictionary created at {filepath}")
        return True
        
    except Exception as e:
        print(f"[INIT] Error creating placeholder dictionary: {e}")
        return False

# -- Save compiled ML dictionary to file --
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

# -- Merge new design data into existing one --
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

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                     3. Material & Parameter Intelligence                   ║
# ╚════════════════════════════════════════════════════════════════════════════╝

# # -- Detect if user is asking for material change, component-specific edit, or comparison --
# def detect_change_request(user_input):
#     """Detect what type of change the user is requesting"""
#     user_lower = user_input.lower()
    
#     # Overall material keywords
#     overall_materials = {
#         "timber": "timber", "wood": "timber", "timber mass": "timber_mass", 
#         "mass timber": "timber_mass", "timber frame": "timber_frame",
#         "concrete": "concrete", "steel": "steel", "brick": "brick", 
#         "earth": "earth", "adobe": "earth", "straw": "straw"
#     }
    
#     # Component-specific keywords
#     component_keywords = {
#         # Wall components
#         "wall": "wall", "exterior wall": "ew", "ext wall": "ew", "external wall": "ew",
#         "interior wall": "iw", "int wall": "iw", "internal wall": "iw",
        
#         # Insulation components  
#         "wall insulation": "ew_ins", "exterior wall insulation": "ew_ins",
#         "roof insulation": "ro_ins", "slab insulation": "es_ins",
        
#         # Roof components
#         "roof": "roof", "roof partition": "ro_par",
        
#         # Slab components
#         "slab": "slab", "floor": "slab", "slab partition": "is_par"
#     }
    
#     # Material types for components
#     wall_materials = ["brick", "concrete", "earth", "straw", "timber_frame", "timber_mass"]
#     insulation_materials = ["cellulose", "cork", "eps", "glass_wool", "mineral_wool", "wood_fiber", "xps", "expanded_glass"]
    
#     # Check for overall material change
#     for material_keyword, material_name in overall_materials.items():
#         if material_keyword in user_lower and any(word in user_lower for word in ["change", "switch", "use", "make", "set", "material", "to"]):
#             return {
#                 "type": "overall_material",
#                 "material": material_name,
#                 "component": None
#             }
    
#     # Check for component-specific changes
#     for component_keyword, component_code in component_keywords.items():
#         if component_keyword in user_lower:
#             # Check what material they want for this component
#             for material in wall_materials + insulation_materials:
#                 if material in user_lower or material.replace("_", " ") in user_lower:
#                     return {
#                         "type": "component_specific",
#                         "material": material,
#                         "component": component_code
#                     }
    
#     # Check for material questions/comparisons
#     for material_keyword, material_name in overall_materials.items():
#         if material_keyword in user_lower and any(word in user_lower for word in ["?", "or", "which", "what", "should", "better", "choose"]):
#             return {
#                 "type": "material_question",
#                 "material": material_name,
#                 "component": None
#             }
    
#     return None

# -- Apply overall material change across multiple components --
def apply_overall_material_change(material_name):
    """Apply overall material change using MaterialMapper logic"""
    try:
        mapper = MaterialMapper()
        parameters = mapper.map_simple_material_to_parameters(material_name)

        # If beams/columns are influenced by overall material, set BC accordingly
        if material_name in mapper.material_mappings.get("Beams_Columns", {}):
            parameters["BC"] = mapper.material_mappings["Beams_Columns"][material_name]

        print(f"[OVERALL MATERIAL] Changing to {material_name}: {parameters}")

        success = update_compiled_ml_data_with_changes(parameters)

        if success:
            return f"Changed overall building material to {material_name.replace('_', ' ')}"
        else:
            return f"Updated material selection to {material_name.replace('_', ' ')}"

    except Exception as e:
        print(f"[OVERALL MATERIAL] Error: {e}")
        return f"Selected {material_name.replace('_', ' ')} material"

# -- Apply material change to a specific component (e.g., only roof, only insulation) --
def apply_component_specific_change(component, material):
    """Apply component-specific material change"""
    try:
        mapper = MaterialMapper()

        # Map component codes to parameter keys
        component_mapping = {
            "ew": "EW_PAR",            # Exterior wall partition
            "ew_ins": "EW_INS",        # Exterior wall insulation
            "iw": "IW_PAR",            # Interior wall partition
            "wall": "EW_PAR",          # Default wall to exterior wall
            "roof": "RO_PAR",          # Roof partition
            "ro_par": "RO_PAR",        # Roof partition
            "ro_ins": "RO_INS",        # Roof insulation
            "slab": "IS_PAR",          # Interior slab partition
            "is_par": "IS_PAR",        # Interior slab partition
            "es_ins": "ES_INS",        # Exterior slab insulation
            "bc": "BC",                # Beams and columns
            "bc_material": "BC"        # Alias for beams/columns
        }

        param_key = component_mapping.get(component.lower())
        if not param_key:
            return f"Updated {component} to {material}"

        category = mapper.get_category_for_param(param_key)
        if category and material in mapper.material_mappings.get(category, {}):
            material_value = mapper.material_mappings[category][material]

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

# -- Update compiled_ml_data.json with new parameter values --
def update_compiled_ml_data_with_changes(parameter_updates):
    """Update compiled_ml_data.json with new parameter values"""
    try:
        from collections import OrderedDict
        
        ml_data_path = os.path.join("knowledge", "compiled_ml_data.json")
        
        # Read existing data
        if os.path.exists(ml_data_path):
            with open(ml_data_path, 'r') as f:
                current_data = json.load(f)
        else:
            # Create default structure if file doesn't exist
            current_data = {
                "EW_PAR": 1, "EW_INS": 2, "IW_PAR": 1, "ES_INS": 1,
                "IS_PAR": 0, "RO_PAR": 0, "RO_INS": 7, "WWR": 0.3,
                "BC": 2,  # Default: timber
                "Typology": 1,  # Default: L-shape
                "A/V": 0.4,
                "Volume(m3)": 1000.0,
                "VOL/VOLBBOX": 1.0
            }

        
        # Update with new parameters
        for param_key, param_value in parameter_updates.items():
            current_data[param_key] = param_value
            print(f"[ML UPDATE] {param_key}: {param_value}")
        
        # Maintain proper order
        ordered_data = OrderedDict()
        key_order = ["EW_PAR", "EW_INS", "IW_PAR", "ES_INS", "IS_PAR", "RO_PAR", "RO_INS", "WWR", "BC", "Typology", "A/V", "Volume(m3)", "VOL/VOLBBOX"
]
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

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                         4. Conversation Flow & State                       ║
# ╚════════════════════════════════════════════════════════════════════════════╝


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                5. Versioning, Suggestions & Query Handlers                ║
# ╚════════════════════════════════════════════════════════════════════════════╝

# === Version utilities (used throughout Group 5) ===
from utils.version_analysis_utils import (
    # list_all_version_files, # it is already used in version_analysis_utils.py 
    # load_specific_version, # it is already used in version_analysis_utils.py 
    summarize_version_outputs,
    get_best_version,
    extract_versions_from_input,
    summarize_versions_data,
    load_version_details
)

# -- Answer user questions using design inputs/outputs --
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

# -- Suggest practical, data-driven design improvements --
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

# -- Convert ML parameter dictionary to readable summary for user --
def generate_user_summary(ml_dict):
    """Turn model inputs into a readable summary"""
    material_map = {
        0: "brick", 1: "concrete", 2: "earth", 3: "straw", 4: "timber frame", 5: "mass timber"
    }
    insulation_map = {
        0: "cellulose", 1: "cork", 2: "EPS", 3: "glass wool", 4: "mineral wool",
        5: "wood fiber", 6: "XPS", 7: "XPS"  # reused for roof
    }
    structure_map = ["concrete", "timber frame", "mass timber"]

    try:
        summary = f"Updated design with:\n"
        summary += f"• Exterior walls: {material_map.get(ml_dict['EW_PAR'], 'unknown')} + {insulation_map.get(ml_dict['EW_INS'], 'unknown')} insulation\n"
        summary += f"• Interior walls: {material_map.get(ml_dict['IW_PAR'], 'unknown')}\n"
        summary += f"• Roof: {structure_map[ml_dict['RO_PAR']]} + {insulation_map.get(ml_dict['RO_INS'], 'unknown')} insulation\n"
        summary += f"• Slab: {structure_map[ml_dict['IS_PAR']]}\n"
        summary += f"• Structure (beams/columns): {structure_map[ml_dict['BC']]}\n"
        summary += f"• WWR: {int(ml_dict['WWR'] * 100)}%\n"
        summary += f"• GFA: {ml_dict['Volume(m3)']} m³\n"
        return summary
    except Exception as e:
        print(f"[SUMMARY ERROR] {e}")
        return "Design updated successfully (could not summarize changes)."


# -- Suggest a change and update model inputs via JSON patching --
def suggest_change(user_prompt, design_data):
        # --- Load current parameters from file ---
        compiled_path = os.path.join("knowledge", "compiled_ml_data.json")
        with open(compiled_path, "r", encoding="utf-8") as f:
            current_parameters = json.load(f)

        # --- Construct the system prompt ---
        system_prompt = f"""
    You are a design assistant helping update building parameters.

    The user will describe a design change (e.g., "Change exterior wall insulation to mineral wool"). You must:

    1. Read the current parameters below.
    2. Modify ONLY the parameters explicitly mentioned by the user.
    3. Leave all other values unchanged.
    4. Output a full dictionary with exactly these 13 keys:
    - Typology, WWR, EW_PAR, EW_INS, IW_PAR, ES_INS, IS_PAR, RO_PAR, RO_INS, BC, A/V, Volume(m3), VOL/VOLBBOX

    DO NOT include explanations or any text. Respond ONLY with a plain JSON dictionary.

    If the user mentions "structure", "frame", "beams", or "columns", update the `BC` parameter accordingly.

    ### Current Parameters:
    {json.dumps(current_parameters, indent=2)}

    ### Parameter Options:
    - Typology: BLOCK=0, L-SHAPE=1, C-SHAPE=2, COURTYARD=3
    - WWR: VERY LOW=0, LOW=1, MODERATE=2, HIGH=3
    - EW_PAR / IW_PAR: BRICK=0, CONCRETE=1, EARTH=2, STRAW=3, TIMBER FRAME=4, TIMBER MASS=5
    - EW_INS: CELLULOSE=0, CORK=1, EPS=2, GLASS WOOL=3, MINERAL WOOL=4, WOOD FIBER=5
    - ES_INS: EXTRUDED GLASS=0, XPS=1
    - IS_PAR / RO_PAR: CONCRETE=0, TIMBER FRAME=1, TIMBER MASS=2
    - RO_INS: CELLULOSE=0, CORK=1, EPS=2, EXTRUDED GLASS=3, GLASS WOOL=4, MINERAL WOOL=5, WOOD FIBER=6, XPS=7
    - A/V, Volume(m3), VOL/VOLBBOX: floats from geometry system
    - BC (Beams & Columns STRUCTURE): STEEL=0, CONCRETE=1, TIMBER=2 ← can be changed by user prompts like "change beams to steel"

    """

        # --- Call the LLM ---
        response = client.chat.completions.create(
            model=completion_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        raw_response = response.choices[0].message.content
        print(f"[RAW LLM RESPONSE]\n{raw_response}")

        # --- Extract and parse the JSON ---
        def extract_json_block(text):
            match = re.search(r'\{[\s\S]*?\}', text)
            return match.group(0).strip() if match else None

        REQUIRED_KEYS = {
            "Typology", "WWR", "EW_PAR", "EW_INS", "IW_PAR", "ES_INS",
            "IS_PAR", "RO_PAR", "RO_INS", "BC", "A/V", "Volume(m3)", "VOL/VOLBBOX"
        }

        PROTECTED_KEYS = {"A/V", "Volume(m3)", "VOL/VOLBBOX"}

        default_inputs = {
            "Typology": 1, "WWR": 2, "EW_PAR": 0, "EW_INS": 0, "IW_PAR": 0,
            "ES_INS": 0, "IS_PAR": 0, "RO_PAR": 0, "RO_INS": 0, "BC": 2,
            "A/V": 0.4, "Volume(m3)": 1000.0, "VOL/VOLBBOX": 1.0
        }

        def parse_and_validate_model_response(response_text, default_inputs):
            try:
                parsed = json.loads(response_text)
                if not isinstance(parsed, dict):
                    raise ValueError("Parsed content is not a dictionary.")

                user_prompt_lower = user_prompt.lower()
                if "beam" in user_prompt_lower or "column" in user_prompt_lower:
                    if "steel" in user_prompt_lower:
                        parsed["BC"] = 0
                    elif "concrete" in user_prompt_lower:
                        parsed["BC"] = 1
                    elif "timber" in user_prompt_lower:
                        parsed["BC"] = 2
                    print(f"[FORCED STRUCTURE OVERRIDE] Detected BC update in user prompt → BC = {parsed['BC']}")

                missing = REQUIRED_KEYS - parsed.keys()
                for key in missing:
                    print(f"[VALIDATION] Missing key: {key} → using default")
                    parsed[key] = default_inputs[key]

                for key in PROTECTED_KEYS:
                    if key in parsed and key in current_parameters:
                        if parsed[key] != current_parameters[key]:
                            print(f"[PROTECTION] Ignoring unauthorized edit to {key}")
                            parsed[key] = current_parameters[key]

                float_keys = {"A/V", "Volume(m3)", "VOL/VOLBBOX"}
                for key in float_keys:
                    parsed[key] = float(parsed[key])
                for key in REQUIRED_KEYS - float_keys:
                    parsed[key] = int(parsed[key])

                return parsed
            except Exception as e:
                raise ValueError(f"Invalid model response: {e}")

        cleaned_json = extract_json_block(raw_response)

        try:
            validated_dict = parse_and_validate_model_response(cleaned_json, default_inputs)

            merged_result = current_parameters.copy()
            merged_result.update(validated_dict)

            save_ml_dictionary(merged_result)
        except ValueError as e:
            print(f"❌ Error validating LLM output: {e}")
            with open("invalid_llm_output.json", "w", encoding="utf-8") as f:
                f.write(raw_response)
            return "⚠️ Unable to process design change due to invalid output."

        # --- Run ML predictor ---
        def run_ml_predictor():
            project_root = os.path.dirname(os.path.abspath(__file__))
            predictor_path = os.path.join(project_root, "utils", "ML_predictor.py")
            python_path = sys.executable

            if not os.path.exists(predictor_path):
                print("⚠️ ML Predictor script not found.")
                return

            try:
                result = subprocess.run(
                    [python_path, predictor_path],
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    check=True
                )
                print("ML Predictor Output:\n", result.stdout)
            except subprocess.CalledProcessError as e:
                print("ML Predictor failed:\n", e.stderr)

        run_ml_predictor()



        # --- Load new output for comparison ---
        try:
            with open("knowledge/ml_output.json", "r", encoding="utf-8") as f:
                new_data = json.load(f)
        except Exception as e:
            print(f"[COMPARE] Failed to load new output: {e}")
            return "✅ Change saved, but result analysis unavailable."

        previous_data = get_last_version_data()

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
 
# -- Compare specific versions and explain differences --
def compare_versions_summary(user_input):
    """Compare multiple versions based on decoded inputs and outputs, with an LLM-crafted concise summary."""
    try:
        version_names = extract_versions_from_input(user_input)
        if not version_names or len(version_names) < 2:
            return "Please specify at least two versions to compare (e.g., 'Compare V2 and V5')."

        data = summarize_versions_data(version_names)
        if not data:
            return "No matching data found for the specified versions."

        # Build raw summary table
        response_lines = ["🔍 Version Comparison:"]
        for version in version_names:
            details = data.get(version, {})
            inputs = details.get("inputs_decoded", {})
            outputs = details.get("outputs", {})
            gwp = outputs.get("GWP total", "N/A")
            eui = outputs.get("Energy Intensity - EUI (kWh/m²a)", "N/A")
            oc = outputs.get("Operational Carbon (kg CO2e/m²a GFA)", "N/A")
            ec = outputs.get("Embodied Carbon A-D (kg CO2e/m²a GFA)", "N/A")

            response_lines.append(
                f"\n{version}\n"
                f"- GWP: {gwp} kg CO2e/m²\n"
                f"- EUI: {eui}\n"
                f"- Operational: {oc}\n"
                f"- Embodied A-D: {ec}"
            )

        # Build structured prompt for LLM
        llm_versions_info = "\n".join([
            f"{v}:\nInputs: {json.dumps(data[v].get('inputs_decoded', {}))}\n"
            f"Outputs: {json.dumps(data[v].get('outputs', {}))}\n"
            for v in version_names if v in data
        ])

        prompt = f"""
You are a sustainability assistant helping architects compare design alternatives.

- Summarize the main differences across these {len(version_names)} versions.
- Focus on GWP, materials, insulation, and energy usage.
- Be concise and insightful. Write a single paragraph (max 3 sentences).
- Avoid bullet points and technical jargon.

{llm_versions_info}
"""

        llm_response = client.chat.completions.create(
            model=completion_model,
            messages=[
                {"role": "system", "content": prompt}
            ]
        )

        summary = llm_response.choices[0].message.content.strip()
        return f"{summary}\n\n🧾 Raw data:\n" + "\n".join(response_lines)

    except Exception as e:
        print(f"[COMPARE VERSIONS ERROR] {e}")
        return "⚠️ Could not compare versions due to an internal error."

# -- Return summary of all known version outputs --
def query_version_outputs():
    """Return a brief summary of all version outputs"""
    try:
        versions = summarize_version_outputs()
        summary_lines = [
            f"• {v['version']}: {v['outputs'].get('GWP total (kg CO2e/m²a GFA)', 'N/A')} kg CO2e/m²"
            for v in versions
        ]
        return "Project Versions:\n" + "\n".join(summary_lines)
    except Exception as e:
        return f"Could not summarize version outputs: {e}"

# -- Return best performing version based on a given metric --
def get_best_version_summary():
    """Return a human-readable summary of the best version based on GWP"""
    try:
        best, value = get_best_version(metric="GWP total (kg CO2e/m²a GFA)")
        if best is None or value is None or value == float("inf"):
            return "No suitable version found for comparison."
        return f"The best performing design is **{best}** with the lowest GWP: **{value:.2f} kg CO2e/m²a**."
    except Exception as e:
        print(f"[BEST VERSION SUMMARY ERROR] {e}")
        return "Error while evaluating the best performing version."

# -- Optional helper: get latest saved version data (V*.json) --
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


