import json
import random
import re
import traceback
from server.config import *

# === TYPOLOGY VALIDATION RULES ===
TYPOLOGY_RULES = {
    "block": {"width_min": 5, "width_max": 12, "depth_min": 5, "depth_max": 5},
    "L-shape": {"width_min": 6, "width_max": 15, "depth_min": 6, "depth_max": 15},
    "U-shape": {"width_min": 6, "width_max": 15, "depth_min": 6, "depth_max": 15},
    "courtyard": {"width_min": 15, "width_max": float('inf'), "depth_min": 15, "depth_max": float('inf')}
}

MAX_LEVELS = 10
VOXEL_SIZE = 3  # meters

def round_to_voxel_multiple(dimension_m):
    """Round dimension to nearest multiple of voxel size (3m)"""
    return round(dimension_m / VOXEL_SIZE) * VOXEL_SIZE

def validate_dimensions_for_typology(typology, width_m, depth_m):
    """Validate if dimensions fit within typology rules"""
    if typology not in TYPOLOGY_RULES:
        return True, "Unknown typology, allowing dimensions"
    
    rules = TYPOLOGY_RULES[typology]
    width_voxels = width_m / VOXEL_SIZE
    depth_voxels = depth_m / VOXEL_SIZE
    
    # Check width
    if width_voxels < rules["width_min"] or width_voxels > rules["width_max"]:
        return False, f"Width {width_m}m ({width_voxels:.1f} voxels) outside range {rules['width_min']}-{rules['width_max']} voxels for {typology}"
    
    # Check depth  
    if depth_voxels < rules["depth_min"] or depth_voxels > rules["depth_max"]:
        return False, f"Depth {depth_m}m ({depth_voxels:.1f} voxels) outside range {rules['depth_min']}-{rules['depth_max']} voxels for {typology}"
    
    return True, "Valid dimensions"

def suggest_parameter_value(parameter_type, existing_data):
    """AI suggests parameter values based on context"""
    import random
    
    if parameter_type == "typology":
        # Suggest based on building type if available
        building_type = existing_data.get("building_type", "")
        if building_type in ["residential", "hotel"]:
            return random.choice(["block", "L-shape", "U-shape"])
        elif building_type in ["office", "hospital", "school"]:
            return random.choice(["block", "courtyard"])
        else:
            return random.choice(["block", "L-shape", "U-shape", "courtyard"])
    
    elif parameter_type == "number_of_levels":
        building_type = existing_data.get("building_type", "")
        if building_type == "residential":
            return random.choice([3, 4, 5, 6])
        elif building_type in ["office", "hospital"]:
            return random.choice([4, 5, 6, 7, 8])
        else:
            return random.choice([3, 4, 5, 6])
    
    elif parameter_type == "width_m":
        typology = existing_data.get("geometry", {}).get("typology", "")
        if typology == "courtyard":
            return random.choice([45, 48, 51, 54])  # Larger for courtyards
        else:
            return random.choice([15, 18, 21, 24, 27])
    
    elif parameter_type == "depth_m":
        typology = existing_data.get("geometry", {}).get("typology", "")
        if typology == "courtyard":
            return random.choice([45, 48, 51, 54])  # Larger for courtyards
        else:
            return random.choice([15, 18, 21, 24, 27])
    
    elif parameter_type == "materiality":
        climate = existing_data.get("climate", "")
        if climate == "cold":
            return random.choice(["timber_mass", "brick", "concrete"])
        elif climate == "hot-humid":
            return random.choice(["concrete", "brick"])
        elif climate == "arid":
            return random.choice(["earth", "concrete", "brick"])
        else:
            return random.choice(["brick", "concrete", "timber_frame", "timber_mass"])
    
    elif parameter_type == "climate":
        return random.choice(["temperate", "cold", "hot-humid", "arid"])
    
    elif parameter_type == "wwr":
        building_type = existing_data.get("building_type", "")
        if building_type in ["office", "school"]:
            return round(random.uniform(0.35, 0.5), 2)  # Higher for offices/schools
        else:
            return round(random.uniform(0.25, 0.4), 2)  # Standard range
    
    elif parameter_type == "building_type":
        return random.choice(["residential", "office", "mixed-use", "retail"])
    
    return None

def extract_all_parameters_from_input(user_input, current_state="unknown"):
    """Enhanced extraction that catches all parameter mentions with context awareness + AI suggestions"""
    try:
        extracted = {}
        input_lower = user_input.lower().strip()
        
        # Context-aware extraction - if we're asking for a specific thing, prioritize that
        if current_state == "geometry_levels" and re.match(r'^\s*\d+\s*$', input_lower):
            levels = min(int(input_lower), MAX_LEVELS)
            extracted["geometry"] = {"number_of_levels": levels}
            return extracted
        
        if current_state == "geometry_width" and re.match(r'^\s*\d+\s*$', input_lower):
            width = round_to_voxel_multiple(float(input_lower))
            extracted["geometry"] = {"width_m": width}
            return extracted
            
        if current_state == "geometry_depth" and re.match(r'^\s*\d+\s*$', input_lower):
            depth = round_to_voxel_multiple(float(input_lower))
            extracted["geometry"] = {"depth_m": depth}
            return extracted

        # AI SUGGESTION DETECTION
        suggestion_patterns = [
            "choose for me", "you choose", "you decide", "surprise me", "recommend", 
            "suggest", "pick for me", "what do you think", "your choice", "up to you",
            "i dont know", "not sure", "help me choose", "best option", "good choice"
        ]
        
        wants_ai_suggestion = any(pattern in input_lower for pattern in suggestion_patterns)
        
        # Extract number of levels
        level_patterns = [
            r'(\d+)\s*(?:storey|story|level|floor)s?',
            r'(\d+)\s*levels?',
            r'(\d+)[-\s]*level',
            r'(\d+)[-\s]*storey'
        ]
        for pattern in level_patterns:
            match = re.search(pattern, input_lower)
            if match:
                levels = min(int(match.group(1)), MAX_LEVELS)
                if "geometry" not in extracted:
                    extracted["geometry"] = {}
                extracted["geometry"]["number_of_levels"] = levels
                break
        
        # Extract typology
        typology_patterns = {
            "L-shape": ["l-shape", "l shape", "l shaped", "l-shaped", "l building"],
            "U-shape": ["u-shape", "u shape", "u shaped", "u-shaped", "u building"],
            "courtyard": ["courtyard", "court yard", "court", "atrium"],
            "block": ["block", "rectangular", "simple block", "box"]
        }
        
        for typology, patterns in typology_patterns.items():
            if any(pattern in input_lower for pattern in patterns):
                if "geometry" not in extracted:
                    extracted["geometry"] = {}
                extracted["geometry"]["typology"] = typology
                break
        
        # Extract dimensions - paired first
        dimension_patterns = [
            r'(\d+)m?\s*(?:by|x|×)\s*(\d+)m?',
            r'(\d+)\s*(?:meter|m)\s*(?:by|x|×)\s*(\d+)\s*(?:meter|m)?',
            r'(\d+)\s*by\s*(\d+)',
            r'(\d+)\s*wide.*?(\d+)\s*deep',
            r'width.*?(\d+).*?depth.*?(\d+)'
        ]
        
        dimensions_found = False
        for pattern in dimension_patterns:
            match = re.search(pattern, input_lower)
            if match and len(match.groups()) >= 2:
                width = float(match.group(1))
                depth = float(match.group(2))
                if "geometry" not in extracted:
                    extracted["geometry"] = {}
                extracted["geometry"]["width_m"] = round_to_voxel_multiple(width)
                extracted["geometry"]["depth_m"] = round_to_voxel_multiple(depth)
                dimensions_found = True
                break
        
        # Individual width/depth only if no paired dimensions found
        if not dimensions_found:
            # Width patterns
            if "width" in input_lower and "depth" not in input_lower:
                width_match = re.search(r'(\d+)', input_lower)
                if width_match:
                    width = float(width_match.group(1))
                    if "geometry" not in extracted:
                        extracted["geometry"] = {}
                    extracted["geometry"]["width_m"] = round_to_voxel_multiple(width)
            
            # Depth patterns
            elif "depth" in input_lower and "width" not in input_lower:
                depth_match = re.search(r'(\d+)', input_lower)
                if depth_match:
                    depth = float(depth_match.group(1))
                    if "geometry" not in extracted:
                        extracted["geometry"] = {}
                    extracted["geometry"]["depth_m"] = round_to_voxel_multiple(depth)
        
        # Extract building type
        building_patterns = {
            "residential": ["residential", "apartment", "housing", "house", "home", "flat", "condo"],
            "office": ["office", "commercial", "workplace", "business"],
            "hotel": ["hotel", "hospitality", "accommodation"],
            "mixed-use": ["mixed-use", "mixed use", "multi-use"],
            "museum": ["museum", "gallery", "cultural"],
            "hospital": ["hospital", "medical", "healthcare"],
            "school": ["school", "educational", "university", "college"],
            "retail": ["retail", "shop", "store", "shopping"],
            "warehouse": ["warehouse", "storage", "industrial"],
            "restaurant": ["restaurant", "cafe", "dining"]
        }
        
        for building_type, patterns in building_patterns.items():
            if any(pattern in input_lower for pattern in patterns):
                extracted["building_type"] = building_type
                break
        
        # Extract materials
        material_patterns = {
            "brick": ["brick", "masonry"],
            "concrete": ["concrete", "cement"],
            "earth": ["earth", "adobe", "mud"],
            "straw": ["straw", "straw bale"],
            "timber_frame": ["timber frame", "wood frame", "wooden frame"],
            "timber_mass": ["timber mass", "mass timber", "timber", "wood", "wooden"]
        }
        
        for material, patterns in material_patterns.items():
            if any(pattern in input_lower for pattern in patterns):
                extracted["materiality"] = material
                break
        
        # Extract climate
        climate_patterns = {
            "cold": ["cold", "winter", "freezing", "snow"],
            "hot-humid": ["hot humid", "hot", "tropical", "humid", "summer"],
            "arid": ["arid", "dry", "desert"],
            "temperate": ["temperate", "mild", "moderate"]
        }
        
        for climate, patterns in climate_patterns.items():
            if any(pattern in input_lower for pattern in patterns):
                extracted["climate"] = climate
                break
        
        # Extract WWR
        wwr_patterns = [
            r'(\d+)%?\s*(?:window|glazing|glass)',
            r'(?:window|wwr).*?(\d+)%?',
            r'(\d+)%?\s*wwr',
            r'(\d+)%?\s*windows'
        ]
        for pattern in wwr_patterns:
            match = re.search(pattern, input_lower)
            if match:
                percentage = float(match.group(1))
                if percentage > 1:
                    percentage = percentage / 100
                extracted["wwr"] = round(percentage, 2)
                break
        
        # Extract modeling preference
        modeling_patterns = {
            False: ["help me model", "model it", "model for me", "you model", "do it for me", "generate it", "create it", "you help"],
            True: ["i model", "myself", "i will model", "i do it", "let me model"]
        }
        
        for self_modeling, patterns in modeling_patterns.items():
            if any(pattern in input_lower for pattern in patterns):
                extracted["self_modeling"] = self_modeling
                break
        
        # Mark if user wants AI suggestions
        if wants_ai_suggestion:
            extracted["wants_ai_suggestion"] = True
        
        return extracted
        
    except Exception as e:
        print(f"Error in parameter extraction: {str(e)}")
        return {}

def merge_design_data(existing_data, new_data):
    """Intelligently merge new extracted data with existing design data"""
    merged = existing_data.copy()
    
    for key, value in new_data.items():
        if key == "geometry":
            if "geometry" not in merged:
                merged["geometry"] = {}
            for geom_key, geom_value in value.items():
                merged["geometry"][geom_key] = geom_value
        else:
            merged[key] = value
    
    # Auto-calculate height category if levels are provided
    if "geometry" in merged and "number_of_levels" in merged["geometry"]:
        levels = merged["geometry"]["number_of_levels"]
        if levels <= 3:
            merged["geometry"]["height"] = "low-rise"
        elif levels <= 12:
            merged["geometry"]["height"] = "mid-rise"
        else:
            merged["geometry"]["height"] = "high-rise"
    
    return merged

def determine_next_missing_parameter(design_data):
    """Determine what parameter is still missing"""
    
    # First check if we have any data at all - if not, ask the opening question
    if not design_data or len(design_data) == 0:
        return "initial", "What would you like to build today?"
    
    # Check modeling preference (most important after we know what they are building)
    if "self_modeling" not in design_data:
        return "modeling_preference", "Will you model it yourself, or should I model it for you?"
    
    # If LLM modeling, check geometry requirements
    if not design_data.get("self_modeling", True):
        geometry = design_data.get("geometry", {})
        
        if "typology" not in geometry:
            return "geometry_typology", "What building shape? (block, L-shape, U-shape, courtyard)"
        
        if "number_of_levels" not in geometry:
            return "geometry_levels", f"How many levels? (1-{MAX_LEVELS})"
            
        if "width_m" not in geometry:
            return "geometry_width", "What width in meters?"
            
        if "depth_m" not in geometry:
            return "geometry_depth", "What depth in meters?"
            
        # GEOMETRY COMPLETE - trigger generation but continue collecting other params
        # Check if we have all geometry parameters
        if all(key in geometry for key in ["typology", "number_of_levels", "width_m", "depth_m"]):
            # Mark geometry as ready for generation
            design_data["geometry_ready"] = True
    
    # Continue with other parameters (building type is optional now)
    if "materiality" not in design_data:
        return "materiality", "What material? (brick, concrete, timber, earth, straw)"
        
    if "climate" not in design_data:
        return "climate", "What climate? (cold, hot, arid, temperate)"
        
    if "wwr" not in design_data:
        return "wwr", "What window percentage? (like 30% or 40%)"
    
    # Everything complete!
    return "complete", "Perfect! All parameters complete. Ready to generate!"

def manage_conversation_state(current_state, user_input, design_data):
    """
    Smart conversation manager that extracts parameters and skips already-answered questions
    Returns: (new_state, response, updated_design_data)
    """
    
    # Handle empty input - KEY FOR INITIAL QUESTION
    if not user_input.strip():
        next_state, next_question = determine_next_missing_parameter(design_data)
        return next_state, next_question, design_data
    
    # Extract parameters from user input
    extracted_params = extract_all_parameters_from_input(user_input, current_state)
    
    # Handle AI suggestions if user wants them
    if extracted_params.get("wants_ai_suggestion", False):
        suggested_params = {}
        
        # Determine what parameter we're currently asking for
        if current_state == "geometry_typology":
            suggested_value = suggest_parameter_value("typology", design_data)
            if suggested_value:
                suggested_params["geometry"] = {"typology": suggested_value}
        
        elif current_state == "geometry_levels":
            suggested_value = suggest_parameter_value("number_of_levels", design_data)
            if suggested_value:
                suggested_params["geometry"] = {"number_of_levels": suggested_value}
        
        elif current_state == "geometry_width":
            suggested_value = suggest_parameter_value("width_m", design_data)
            if suggested_value:
                suggested_params["geometry"] = {"width_m": suggested_value}
        
        elif current_state == "geometry_depth":
            suggested_value = suggest_parameter_value("depth_m", design_data)
            if suggested_value:
                suggested_params["geometry"] = {"depth_m": suggested_value}
        
        elif current_state == "materiality":
            suggested_value = suggest_parameter_value("materiality", design_data)
            if suggested_value:
                suggested_params["materiality"] = suggested_value
        
        elif current_state == "climate":
            suggested_value = suggest_parameter_value("climate", design_data)
            if suggested_value:
                suggested_params["climate"] = suggested_value
        
        elif current_state == "wwr":
            suggested_value = suggest_parameter_value("wwr", design_data)
            if suggested_value:
                suggested_params["wwr"] = suggested_value
        
        elif current_state == "building_type":
            suggested_value = suggest_parameter_value("building_type", design_data)
            if suggested_value:
                suggested_params["building_type"] = suggested_value
        
        # Special case: if user says "choose everything" or similar
        choose_all_patterns = [
            "choose everything", "pick everything", "decide everything", "all parameters",
            "complete it", "finish it", "make all choices", "fill everything"
        ]
        
        if any(pattern in user_input.lower() for pattern in choose_all_patterns):
            # Fill in ALL missing parameters
            if "self_modeling" not in design_data:
                suggested_params["self_modeling"] = False  # Default to LLM modeling
            
            if not design_data.get("self_modeling", True):
                geometry = design_data.get("geometry", {})
                if "typology" not in geometry:
                    if "geometry" not in suggested_params:
                        suggested_params["geometry"] = {}
                    suggested_params["geometry"]["typology"] = suggest_parameter_value("typology", design_data)
                
                if "number_of_levels" not in geometry:
                    if "geometry" not in suggested_params:
                        suggested_params["geometry"] = {}
                    suggested_params["geometry"]["number_of_levels"] = suggest_parameter_value("number_of_levels", design_data)
                
                if "width_m" not in geometry:
                    if "geometry" not in suggested_params:
                        suggested_params["geometry"] = {}
                    suggested_params["geometry"]["width_m"] = suggest_parameter_value("width_m", design_data)
                
                if "depth_m" not in geometry:
                    if "geometry" not in suggested_params:
                        suggested_params["geometry"] = {}
                    suggested_params["geometry"]["depth_m"] = suggest_parameter_value("depth_m", design_data)
            
            if "materiality" not in design_data:
                suggested_params["materiality"] = suggest_parameter_value("materiality", design_data)
            
            if "climate" not in design_data:
                suggested_params["climate"] = suggest_parameter_value("climate", design_data)
            
            if "wwr" not in design_data:
                suggested_params["wwr"] = suggest_parameter_value("wwr", design_data)
        
        # Merge suggested parameters with extracted ones
        if suggested_params:
            extracted_params = {**suggested_params, **extracted_params}  # Extracted takes priority
            extracted_params["ai_suggested"] = True  # Mark that AI made suggestions
    
    # Merge with existing data
    if extracted_params:
        design_data = merge_design_data(design_data, extracted_params)
    
    # Handle constraints and validation - BUT BE FLEXIBLE
    if "geometry" in design_data and "number_of_levels" in design_data["geometry"]:
        levels = design_data["geometry"]["number_of_levels"]
        if levels > MAX_LEVELS:
            design_data["geometry"]["number_of_levels"] = MAX_LEVELS
    
    # Round dimensions to voxel multiples
    geometry = design_data.get("geometry", {})
    if "width_m" in geometry:
        design_data["geometry"]["width_m"] = round_to_voxel_multiple(geometry["width_m"])
    if "depth_m" in geometry:
        design_data["geometry"]["depth_m"] = round_to_voxel_multiple(geometry["depth_m"])
    
    # CHECK FOR GEOMETRY GENERATION TRIGGER
    should_trigger_geometry = False
    if (not design_data.get("self_modeling", True) and 
        "geometry" in design_data and 
        all(key in design_data["geometry"] for key in ["typology", "number_of_levels", "width_m", "depth_m"]) and
        not design_data.get("geometry_generated", False)):
        
        should_trigger_geometry = True
        design_data["geometry_generated"] = True  # Mark as generated to avoid repeats
    
    # Determine what is still needed
    next_state, next_question = determine_next_missing_parameter(design_data)
    
    # Create response acknowledging what we got
    response_parts = []
    
    if extracted_params:
        acknowledgments = []
        
        # ONLY acknowledge building_type if user actually provided it
        if "building_type" in extracted_params:
            acknowledgments.append(f"building type: {extracted_params['building_type']}")
        
        if "geometry" in extracted_params:
            geom = extracted_params["geometry"]
            if "number_of_levels" in geom:
                levels = geom['number_of_levels']
                if levels > MAX_LEVELS:
                    acknowledgments.append(f"{MAX_LEVELS} levels (capped at maximum)")
                else:
                    acknowledgments.append(f"{levels} levels")
            if "typology" in geom:
                acknowledgments.append(f"{geom['typology']} typology")
            if "width_m" in geom and "depth_m" in geom:
                acknowledgments.append(f"{geom['width_m']}×{geom['depth_m']}m")
            elif "width_m" in geom:
                acknowledgments.append(f"width: {geom['width_m']}m")
            elif "depth_m" in geom:
                acknowledgments.append(f"depth: {geom['depth_m']}m")
        
        if "materiality" in extracted_params:
            acknowledgments.append(f"{extracted_params['materiality']} material")
        
        if "climate" in extracted_params:
            acknowledgments.append(f"{extracted_params['climate']} climate")
        
        if "wwr" in extracted_params:
            acknowledgments.append(f"{int(extracted_params['wwr']*100)}% windows")
        
        if "self_modeling" in extracted_params:
            modeling_pref = "I'll model it" if not extracted_params["self_modeling"] else "you'll model it"
            acknowledgments.append(modeling_pref)
        
        if acknowledgments:
            # Add AI suggestion indicator
            prefix = "AI suggested: " if extracted_params.get("ai_suggested", False) else "Updated: "
            response_parts.append(f"{prefix}{', '.join(acknowledgments)}.")
    
    # Add geometry generation notification
    if should_trigger_geometry:
        response_parts.append("Geometry parameters complete! Generating 3D model...")
    
    # ONLY do validation check if we have complete geometry AND we are complete
    validation_warning = ""
    if (next_state == "complete" and 
        "geometry" in design_data and 
        all(key in design_data["geometry"] for key in ["typology", "width_m", "depth_m"])):
        
        is_valid, validation_msg = validate_dimensions_for_typology(
            design_data["geometry"]["typology"], 
            design_data["geometry"]["width_m"], 
            design_data["geometry"]["depth_m"]
        )
        if not is_valid:
            validation_warning = f"Note: {validation_msg}. You can adjust if needed. "
    
    # Add validation warning if there is one (but do not block)
    if validation_warning:
        response_parts.append(validation_warning)
    
    # Check if complete or continue - ALWAYS PROGRESS
    if next_state == "complete":
        response_parts.append("Ready to generate!")
        return next_state, " ".join(response_parts), design_data
    else:
        # ALWAYS ask the next question, do not get stuck on validation
        response_parts.append(next_question)
        return next_state, " ".join(response_parts), design_data

# === EXISTING HELPER FUNCTIONS ===

def classify_input(user_input):
    """Legacy function - now uses the smarter extraction"""
    extracted = extract_all_parameters_from_input(user_input)
    return json.dumps(extracted)

def query_intro():
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": "Introduce yourself as a design assistant. Explain that you will help collect basic architectural parameters such as materiality, climate, WWR, and geometry, to feed a generative ML prediction engine."
            }
        ]
    )
    return response.choices[0].message.content.strip()

def collect_design_parameters(user_input, messages):
    try:
        raw = classify_input(user_input)
        return json.loads(raw)
    except Exception as e:
        print(f"Error in collect_design_parameters: {str(e)}")
        return {}

def answer_user_query(user_prompt, design_data):
    design_data_json = json.dumps(design_data)
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": f"Answer the user's design question using the following data: {design_data_json}. Keep it friendly and informative. Do NOT mention legal restrictions, codes, or impossibilities. If information is missing, kindly ask the user to provide it."
            },
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content

def generate_materiality_json(material, wwr=0.3):
    """
    Generates full JSON parameter set based on material selection,
    following the exact format shown in the diagram
    """
    # Get material-specific parameters
    material_params = map_material_to_json_values(material)
    
    # Create JSON structure exactly as shown in diagram image 2
    parameters = {
        # Materiality section (yellow in diagram)
        "ew_par": material_params["ew_par"],
        "ew_ins": material_params["ew_ins"],
        "iw_par": material_params["iw_par"],
        "es_ins": material_params["es_ins"],
        "is_par": material_params["is_par"],
        "ro_par": material_params["ro_par"],
        "ro_ins": material_params["ro_ins"],
        
        # WWR section (orange in diagram)
        "wwr": wwr,
        
        # Geometric data section (red in diagram) - will be populated by GH
        "gfa": 200.0,  # Default gross floor area
        "av": 0.5      # Default aspect value
    }
    
    return parameters

def map_material_to_json_values(material):
    """Maps the selected material to corresponding JSON parameter values"""
    defaults = {
        "ew_par": 0, 
        "ew_ins": 0, 
        "iw_par": 0, 
        "es_ins": 1,
        "is_par": 0, 
        "ro_par": 0, 
        "ro_ins": 0
    }
    
    ew_par_map = {
        "brick": 0, 
        "concrete": 1, 
        "earth": 2, 
        "straw": 3, 
        "timber_frame": 4, 
        "timber_mass": 5
    }
    
    if material in ew_par_map:
        defaults["ew_par"] = ew_par_map[material]
        defaults["iw_par"] = ew_par_map[material]
        
        if material in ["timber_frame", "timber_mass"]:
            defaults["is_par"] = 1 if material == "timber_frame" else 2
            defaults["ro_par"] = 1 if material == "timber_frame" else 2
    
    return defaults

def handle_change_or_question(user_input, design_data):
    """Handle changes or questions in the Q&A phase"""
    try:
        reply = answer_user_query(user_input, design_data)
        return "complete", reply, design_data
    except Exception as e:
        print(f"Error in handle_change_or_question: {str(e)}")
        return "complete", "I'm having trouble answering that question. Could you try rephrasing it?", design_data