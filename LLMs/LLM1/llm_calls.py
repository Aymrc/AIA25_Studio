import json
import random
import re
import traceback
from server.config import *

# === ENHANCED TYPOLOGY VALIDATION RULES ===
TYPOLOGY_RULES = {
    "block": {"width_min": 5, "width_max": 12, "depth_min": 5, "depth_max": 12},
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

def extract_all_parameters_from_input(user_input, current_state="unknown", design_data=None):
    """
    ENHANCED parameter extraction that catches all parameter mentions with superior natural language processing
    Now handles complex multi-parameter inputs and context awareness
    """
    try:
        extracted = {}
        input_lower = user_input.lower().strip()
        
        if not input_lower:
            return extracted
            
        design_data = design_data or {}
        
        print(f"[EXTRACTION DEBUG] Input: '{user_input}'")
        print(f"[EXTRACTION DEBUG] Current state: {current_state}")
        
        # === CONTEXT-AWARE SINGLE VALUE EXTRACTION ===
        # When we're asking for a specific parameter and user gives just a number/word
        if current_state == "geometry_levels" and re.match(r'^\s*\d+\s*$', input_lower):
            levels = min(int(input_lower), MAX_LEVELS)
            extracted["geometry"] = {"number_of_levels": levels}
            print(f"[EXTRACTION DEBUG] Context-aware levels: {levels}")
            return extracted
        
        if current_state == "geometry_width" and re.match(r'^\s*\d+\s*$', input_lower):
            width = round_to_voxel_multiple(float(input_lower))
            extracted["geometry"] = {"width_m": width}
            print(f"[EXTRACTION DEBUG] Context-aware width: {width}")
            return extracted
            
        if current_state == "geometry_depth" and re.match(r'^\s*\d+\s*$', input_lower):
            depth = round_to_voxel_multiple(float(input_lower))
            extracted["geometry"] = {"depth_m": depth}
            print(f"[EXTRACTION DEBUG] Context-aware depth: {depth}")
            return extracted
        
        if current_state == "geometry_typology":
            # Match single word typology responses
            for typology in ["block", "L-shape", "U-shape", "courtyard"]:
                if typology.lower().replace("-", "").replace(" ", "") in input_lower.replace("-", "").replace(" ", ""):
                    extracted["geometry"] = {"typology": typology}
                    print(f"[EXTRACTION DEBUG] Context-aware typology: {typology}")
                    return extracted

        # === AI SUGGESTION DETECTION ===
        suggestion_patterns = [
            "choose for me", "you choose", "you decide", "surprise me", "recommend", 
            "suggest", "pick for me", "what do you think", "your choice", "up to you",
            "i dont know", "i don't know", "not sure", "help me choose", "best option", 
            "good choice", "whatever", "anything", "default", "auto", "automatic"
        ]
        
        wants_ai_suggestion = any(pattern in input_lower for pattern in suggestion_patterns)
        
        # === MULTI-PARAMETER EXTRACTION FROM NATURAL LANGUAGE ===
        
        # 1. EXTRACT BUILDING LEVELS/STORIES
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
                levels = min(int(match.group(1)), MAX_LEVELS)
                if "geometry" not in extracted:
                    extracted["geometry"] = {}
                extracted["geometry"]["number_of_levels"] = levels
                print(f"[EXTRACTION DEBUG] Found levels: {levels}")
                break
        
        # 2. EXTRACT BUILDING TYPOLOGY (Enhanced patterns)
        typology_patterns = {
            "L-shape": [
                "l-shape", "l shape", "l shaped", "l-shaped", "l building", "l-form", "l form",
                "ell shape", "ell-shape", "l-type", "l type", "el shape", "el-shape"
            ],
            "U-shape": [
                "u-shape", "u shape", "u shaped", "u-shaped", "u building", "u-form", "u form",
                "horseshoe", "u-type", "u type", "horseshoe shape"
            ],
            "courtyard": [
                "courtyard", "court yard", "court", "atrium", "central court", "inner court",
                "courtyard building", "atrium building", "enclosed court", "internal courtyard"
            ],
            "block": [
                "block", "rectangular", "simple block", "box", "square", "basic block",
                "rectangular building", "box building", "simple", "basic", "standard"
            ]
        }
        
        for typology, patterns in typology_patterns.items():
            if any(pattern in input_lower for pattern in patterns):
                if "geometry" not in extracted:
                    extracted["geometry"] = {}
                extracted["geometry"]["typology"] = typology
                print(f"[EXTRACTION DEBUG] Found typology: {typology}")
                break
        
        # 3. EXTRACT DIMENSIONS (Enhanced with multiple formats)
        
        # 3a. Paired dimensions (priority)
        dimension_patterns = [
            # Standard formats
            r'(\d+)\s*m?\s*(?:by|x|×|and)\s*(\d+)\s*m?',
            r'(\d+)\s*(?:meter|m)s?\s*(?:by|x|×|and)\s*(\d+)\s*(?:meter|m)s?',
            r'(\d+)\s*by\s*(\d+)',
            # Natural language
            r'(\d+)\s*(?:meter|m)s?\s*wide.*?(\d+)\s*(?:meter|m)s?\s*deep',
            r'(\d+)\s*(?:meter|m)s?\s*long.*?(\d+)\s*(?:meter|m)s?\s*wide',
            r'width.*?(\d+).*?depth.*?(\d+)',
            r'length.*?(\d+).*?width.*?(\d+)',
            # Specific order mentions
            r'(\d+)\s*(?:meter|m)s?\s*in\s*width.*?(\d+)\s*(?:meter|m)s?\s*in\s*depth',
            r'(\d+)\s*(?:meter|m)s?\s*width.*?(\d+)\s*(?:meter|m)s?\s*depth'
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
                print(f"[EXTRACTION DEBUG] Found paired dimensions: {width}x{depth}")
                dimensions_found = True
                break
        
        # 3b. Individual dimensions (only if no paired dimensions found)
        if not dimensions_found:
            # Width specific patterns
            width_patterns = [
                r'width.*?(\d+)\s*(?:meter|m)s?',
                r'(\d+)\s*(?:meter|m)s?\s*wide',
                r'width\s*(?:of\s*)?(\d+)',
                r'(\d+)\s*(?:meter|m)s?\s*in\s*width'
            ]
            
            for pattern in width_patterns:
                match = re.search(pattern, input_lower)
                if match and "depth" not in input_lower:  # Only if depth not mentioned
                    width = float(match.group(1))
                    if "geometry" not in extracted:
                        extracted["geometry"] = {}
                    extracted["geometry"]["width_m"] = round_to_voxel_multiple(width)
                    print(f"[EXTRACTION DEBUG] Found width: {width}")
                    break
            
            # Depth specific patterns
            depth_patterns = [
                r'depth.*?(\d+)\s*(?:meter|m)s?',
                r'(\d+)\s*(?:meter|m)s?\s*deep',
                r'depth\s*(?:of\s*)?(\d+)',
                r'(\d+)\s*(?:meter|m)s?\s*in\s*depth'
            ]
            
            for pattern in depth_patterns:
                match = re.search(pattern, input_lower)
                if match and "width" not in input_lower:  # Only if width not mentioned
                    depth = float(match.group(1))
                    if "geometry" not in extracted:
                        extracted["geometry"] = {}
                    extracted["geometry"]["depth_m"] = round_to_voxel_multiple(depth)
                    print(f"[EXTRACTION DEBUG] Found depth: {depth}")
                    break
        
        # 4. EXTRACT BUILDING TYPE (Enhanced patterns)
        building_patterns = {
            "residential": [
                "residential", "apartment", "housing", "house", "home", "flat", "condo",
                "condominium", "apartment building", "residential building", "housing project",
                "residential complex", "living", "dwelling"
            ],
            "office": [
                "office", "commercial", "workplace", "business", "office building",
                "commercial building", "corporate", "work", "administrative"
            ],
            "hotel": [
                "hotel", "hospitality", "accommodation", "resort", "inn", "motel",
                "hotel building", "hospitality building"
            ],
            "mixed-use": [
                "mixed-use", "mixed use", "multi-use", "multiple use", "mixed function",
                "mixed purpose", "combined use"
            ],
            "museum": [
                "museum", "gallery", "cultural", "exhibition", "art museum", "cultural center",
                "cultural building", "exhibition hall"
            ],
            "hospital": [
                "hospital", "medical", "healthcare", "clinic", "medical center",
                "health center", "medical building", "healthcare facility"
            ],
            "school": [
                "school", "educational", "university", "college", "education", "academic",
                "educational building", "campus", "learning center"
            ],
            "retail": [
                "retail", "shop", "store", "shopping", "commercial retail", "shopping center",
                "retail building", "storefront"
            ],
            "warehouse": [
                "warehouse", "storage", "industrial", "logistics", "distribution",
                "storage building", "industrial building"
            ],
            "restaurant": [
                "restaurant", "cafe", "dining", "food service", "eatery", "bistro",
                "restaurant building", "dining establishment"
            ]
        }
        
        for building_type, patterns in building_patterns.items():
            if any(pattern in input_lower for pattern in patterns):
                extracted["building_type"] = building_type
                print(f"[EXTRACTION DEBUG] Found building type: {building_type}")
                break
        
        # 5. EXTRACT MATERIALS (Enhanced patterns)
        material_patterns = {
            "brick": [
                "brick", "masonry", "brick walls", "brick construction", "brick building",
                "masonry construction", "clay brick", "brickwork"
            ],
            "concrete": [
                "concrete", "cement", "concrete walls", "concrete construction",
                "reinforced concrete", "concrete building", "cement construction"
            ],
            "earth": [
                "earth", "adobe", "mud", "earth construction", "earthen", "mud brick",
                "adobe construction", "earth walls", "natural earth"
            ],
            "straw": [
                "straw", "straw bale", "straw construction", "straw bale construction",
                "straw walls", "bale construction"
            ],
            "timber_frame": [
                "timber frame", "wood frame", "wooden frame", "frame construction",
                "timber framing", "wood framing", "frame building"
            ],
            "timber_mass": [
                "timber mass", "mass timber", "timber", "wood", "wooden", "solid timber",
                "heavy timber", "solid wood", "timber construction", "wood construction",
                "wooden construction", "timber building", "wood building"
            ]
        }
        
        for material, patterns in material_patterns.items():
            if any(pattern in input_lower for pattern in patterns):
                extracted["materiality"] = material
                print(f"[EXTRACTION DEBUG] Found material: {material}")
                break
        
        # 6. EXTRACT CLIMATE (Enhanced patterns)
        climate_patterns = {
            "cold": [
                "cold", "winter", "freezing", "snow", "cold climate", "winter climate",
                "snowy", "frigid", "arctic", "cold weather", "cold environment"
            ],
            "hot-humid": [
                "hot humid", "hot", "tropical", "humid", "summer", "hot climate",
                "tropical climate", "humid climate", "hot and humid", "sweltering",
                "muggy", "hot weather"
            ],
            "arid": [
                "arid", "dry", "desert", "arid climate", "dry climate", "desert climate",
                "hot dry", "dry environment", "drought"
            ],
            "temperate": [
                "temperate", "mild", "moderate", "temperate climate", "mild climate",
                "moderate climate", "balanced", "pleasant"
            ]
        }
        
        for climate, patterns in climate_patterns.items():
            if any(pattern in input_lower for pattern in patterns):
                extracted["climate"] = climate
                print(f"[EXTRACTION DEBUG] Found climate: {climate}")
                break
        
        # 7. EXTRACT WWR (Window-to-Wall Ratio) (Enhanced patterns)
        wwr_patterns = [
            r'(\d+)%?\s*(?:window|glazing|glass|windows)',
            r'(?:window|wwr|glazing).*?(\d+)%?',
            r'(\d+)%?\s*wwr',
            r'(\d+)%?\s*windows',
            r'(\d+)\s*percent\s*(?:window|glass|glazing)',
            r'window.*?ratio.*?(\d+)%?',
            r'glazing.*?(\d+)%?'
        ]
        for pattern in wwr_patterns:
            match = re.search(pattern, input_lower)
            if match:
                percentage = float(match.group(1))
                if percentage > 1:
                    percentage = percentage / 100
                extracted["wwr"] = round(min(percentage, 0.9), 2)  # Cap at 90%
                print(f"[EXTRACTION DEBUG] Found WWR: {extracted['wwr']}")
                break
        
        # 8. EXTRACT MODELING PREFERENCE (Enhanced patterns)
        modeling_patterns = {
            False: [  # LLM should model
                "help me model", "model it", "model for me", "you model", "do it for me",
                "generate it", "create it", "you help", "model it for me", "build it",
                "generate geometry", "create geometry", "make it", "you create",
                "ai model", "auto model", "automatic modeling"
            ],
            True: [   # User will model
                "i model", "myself", "i will model", "i do it", "let me model",
                "i'll model", "manual", "by hand", "user model", "self model",
                "i create", "i'll create", "i'll draw", "i draw", "manual modeling"
            ]
        }
        
        for self_modeling, patterns in modeling_patterns.items():
            if any(pattern in input_lower for pattern in patterns):
                extracted["self_modeling"] = self_modeling
                print(f"[EXTRACTION DEBUG] Found modeling preference: {'self' if self_modeling else 'LLM'}")
                break
        
        # === PARAMETER UPDATE DETECTION ===
        # Detect when user wants to change existing parameters
        update_patterns = [
            r'change\s+(?:the\s+)?(\w+)\s+to\s+(.+)',
            r'update\s+(?:the\s+)?(\w+)\s+to\s+(.+)',
            r'set\s+(?:the\s+)?(\w+)\s+to\s+(.+)',
            r'make\s+(?:the\s+)?(\w+)\s+(.+)',
            r'(\w+)\s+should\s+be\s+(.+)',
            r'new\s+(\w+)\s+(?:is\s+)?(.+)'
        ]
        
        for pattern in update_patterns:
            match = re.search(pattern, input_lower)
            if match:
                param_name = match.group(1).strip()
                param_value = match.group(2).strip()
                print(f"[EXTRACTION DEBUG] Update detected: {param_name} -> {param_value}")
                
                # Handle specific parameter updates
                if param_name in ["width", "w"]:
                    width_match = re.search(r'(\d+)', param_value)
                    if width_match:
                        width = round_to_voxel_multiple(float(width_match.group(1)))
                        if "geometry" not in extracted:
                            extracted["geometry"] = {}
                        extracted["geometry"]["width_m"] = width
                        
                elif param_name in ["depth", "d", "length", "l"]:
                    depth_match = re.search(r'(\d+)', param_value)
                    if depth_match:
                        depth = round_to_voxel_multiple(float(depth_match.group(1)))
                        if "geometry" not in extracted:
                            extracted["geometry"] = {}
                        extracted["geometry"]["depth_m"] = depth
                        
                elif param_name in ["levels", "floors", "stories", "height"]:
                    level_match = re.search(r'(\d+)', param_value)
                    if level_match:
                        levels = min(int(level_match.group(1)), MAX_LEVELS)
                        if "geometry" not in extracted:
                            extracted["geometry"] = {}
                        extracted["geometry"]["number_of_levels"] = levels
                        
                elif param_name in ["typology", "shape", "type"]:
                    for typology in ["block", "L-shape", "U-shape", "courtyard"]:
                        if typology.lower().replace("-", "").replace(" ", "") in param_value.replace("-", "").replace(" ", ""):
                            if "geometry" not in extracted:
                                extracted["geometry"] = {}
                            extracted["geometry"]["typology"] = typology
                            break
                            
                elif param_name in ["material", "materials", "materiality"]:
                    for material in ["brick", "concrete", "earth", "straw", "timber_frame", "timber_mass"]:
                        if material.replace("_", " ") in param_value or material.replace("_", "") in param_value.replace(" ", ""):
                            extracted["materiality"] = material
                            break
                            
                elif param_name in ["wwr", "windows", "window", "glazing"]:
                    wwr_match = re.search(r'(\d+)', param_value)
                    if wwr_match:
                        percentage = float(wwr_match.group(1))
                        if percentage > 1:
                            percentage = percentage / 100
                        extracted["wwr"] = round(min(percentage, 0.9), 2)
                        
                elif param_name in ["climate"]:
                    for climate in ["cold", "hot-humid", "arid", "temperate"]:
                        if climate in param_value:
                            extracted["climate"] = climate
                            break
                break
        
        # === AI SUGGESTION HANDLING ===
        if wants_ai_suggestion:
            extracted["wants_ai_suggestion"] = True
            print(f"[EXTRACTION DEBUG] AI suggestion requested")
            
            # Handle "choose everything" requests
            choose_all_patterns = [
                "choose everything", "pick everything", "decide everything", "all parameters",
                "complete it", "finish it", "make all choices", "fill everything",
                "auto complete", "automatic", "default everything", "suggest all"
            ]
            
            if any(pattern in input_lower for pattern in choose_all_patterns):
                extracted["choose_all_parameters"] = True
                print(f"[EXTRACTION DEBUG] Choose all parameters requested")
        
        print(f"[EXTRACTION DEBUG] Final extracted: {extracted}")
        return extracted
        
    except Exception as e:
        print(f"Error in parameter extraction: {str(e)}")
        traceback.print_exc()
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
                print(f"[MERGE DEBUG] Updated geometry.{geom_key} = {geom_value}")
        else:
            merged[key] = value
            print(f"[MERGE DEBUG] Updated {key} = {value}")
    
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
        return "initial", "What would you like to build today? (Feel free to describe your building in detail - I can extract multiple parameters at once!)"
    
    # Check if user is actively drawing geometry
    if design_data.get("user_drawing_detected", False) and not design_data.get("user_geometry_confirmed", False):
        return "user_geometry_confirmation", "I see you're drawing geometry. Is your building design ready for analysis?"
    
    # If user confirmed their geometry, skip geometry collection
    if design_data.get("user_geometry_confirmed", False):
        design_data["self_modeling"] = True  # Set this automatically
    
    # Check modeling preference (most important after we know what they are building)
    if "self_modeling" not in design_data:
        return "modeling_preference", "Will you model the geometry yourself, or should I generate it for you? (You can also describe the building parameters now: typology, dimensions, levels)"
    
    # If LLM modeling, check geometry requirements
    if not design_data.get("self_modeling", True):
        geometry = design_data.get("geometry", {})
        
        if "typology" not in geometry:
            return "geometry_typology", "What building shape? (block, L-shape, U-shape, courtyard) - you can also include dimensions and levels in your answer"
        
        if "number_of_levels" not in geometry:
            return "geometry_levels", f"How many levels? (1-{MAX_LEVELS}) - you can also specify width and depth if you know them"
            
        if "width_m" not in geometry:
            return "geometry_width", "What width in meters? (depth can be specified too)"
            
        if "depth_m" not in geometry:
            return "geometry_depth", "What depth in meters?"
            
        # GEOMETRY COMPLETE - trigger generation but continue collecting other params
        # Check if we have all geometry parameters
        if all(key in geometry for key in ["typology", "number_of_levels", "width_m", "depth_m"]):
            # Mark geometry as ready for generation
            design_data["geometry_ready"] = True
    
    # Continue with other parameters
    if "materiality" not in design_data:
        return "materiality", "What material? (brick, concrete, timber, earth, straw) - you can also include climate and window percentage"
        
    if "climate" not in design_data:
        return "climate", "What climate? (cold, hot-humid, arid, temperate) - window percentage can be added too"
        
    if "wwr" not in design_data:
        return "wwr", "What window percentage? (like 30% or 40%)"
    
    # Everything complete!
    return "complete", "Perfect! All parameters complete. Ready to generate!"

def handle_ai_suggestions(extracted_params, design_data, current_state):
    """Handle AI suggestions when user requests them"""
    suggested_params = {}
    
    if not extracted_params.get("wants_ai_suggestion", False):
        return suggested_params
    
    print(f"[AI SUGGESTION DEBUG] Handling suggestions for state: {current_state}")
    
    # Handle "choose all" requests
    if extracted_params.get("choose_all_parameters", False):
        print(f"[AI SUGGESTION DEBUG] Choosing all parameters")
        
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
            
        if "building_type" not in design_data:
            suggested_params["building_type"] = suggest_parameter_value("building_type", design_data)
    
    else:
        # Handle single parameter suggestions based on current state
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
        
        elif current_state == "modeling_preference":
            suggested_params["self_modeling"] = False  # Default to LLM modeling
    
    if suggested_params:
        print(f"[AI SUGGESTION DEBUG] Generated suggestions: {suggested_params}")
    
    return suggested_params

def manage_conversation_state(current_state, user_input, design_data):
    """
    ENHANCED conversation manager with superior natural language processing and real-time updates
    Returns: (new_state, response, updated_design_data)
    """
    
    print(f"[CONVERSATION DEBUG] State: {current_state}, Input: '{user_input[:50]}...', Current data keys: {list(design_data.keys())}")
    
    # Handle empty input - KEY FOR INITIAL QUESTION
    if not user_input.strip():
        next_state, next_question = determine_next_missing_parameter(design_data)
        print(f"[CONVERSATION DEBUG] Empty input -> {next_state}: {next_question}")
        return next_state, next_question, design_data
    
    # === SPECIAL STATE HANDLING ===
    
    # Handle user geometry confirmation
    if current_state == "user_geometry_confirmation":
        confirmation_yes = any(word in user_input.lower() for word in ["yes", "y", "ready", "done", "finished", "complete", "ok", "confirm"])
        confirmation_no = any(word in user_input.lower() for word in ["no", "n", "not ready", "still working", "not done", "wait"])
        
        if confirmation_yes:
            design_data["user_geometry_confirmed"] = True
            design_data["self_modeling"] = True
            # Remove the detection flag
            design_data.pop("user_drawing_detected", None)
            
            next_state, next_question = determine_next_missing_parameter(design_data)
            response = f"Perfect! I'll use your geometry. {next_question}"
            print(f"[CONVERSATION DEBUG] User confirmed geometry -> {next_state}")
            return next_state, response, design_data
            
        elif confirmation_no:
            # Continue monitoring
            response = "No problem! I'll keep monitoring. Let me know when your geometry is ready, or you can ask me to model it for you instead."
            print(f"[CONVERSATION DEBUG] User geometry not ready, continuing to monitor")
            return current_state, response, design_data
        
        # If unclear response, extract parameters but stay in confirmation state
        else:
            extracted_params = extract_all_parameters_from_input(user_input, current_state, design_data)
            if extracted_params:
                design_data = merge_design_data(design_data, extracted_params)
            response = "I didn't catch that. Is your geometry ready for analysis? (yes/no)"
            return current_state, response, design_data
    
    # === MAIN PARAMETER EXTRACTION ===
    extracted_params = extract_all_parameters_from_input(user_input, current_state, design_data)
    
    # Handle AI suggestions
    if extracted_params.get("wants_ai_suggestion", False):
        suggested_params = handle_ai_suggestions(extracted_params, design_data, current_state)
        # Merge suggested parameters with extracted ones (extracted takes priority)
        if suggested_params:
            extracted_params = {**suggested_params, **extracted_params}
            extracted_params["ai_suggested"] = True
    
    # === SPECIAL PARAMETER HANDLING ===
    
    # Handle "change modeling preference" during conversation
    if "self_modeling" in extracted_params and "self_modeling" in design_data:
        # User is changing their modeling preference
        old_preference = "self-modeling" if design_data["self_modeling"] else "LLM-modeling"
        new_preference = "self-modeling" if extracted_params["self_modeling"] else "LLM-modeling"
        
        if old_preference != new_preference:
            design_data = merge_design_data(design_data, extracted_params)
            
            if extracted_params["self_modeling"]:
                # User wants to model themselves now
                response = f"Switched to self-modeling! You can start drawing your geometry in Rhino. I'll detect when you're ready."
                # Clear any existing geometry generation flags
                design_data.pop("geometry_ready", None)
                design_data.pop("geometry_generated", None)
                design_data["user_drawing_detected"] = True  # Trigger monitoring
                return "user_geometry_confirmation", response, design_data
            else:
                # User wants LLM to model now
                response = f"Switched to LLM modeling! "
                # Check what geometry parameters we need
                next_state, next_question = determine_next_missing_parameter(design_data)
                response += next_question
                return next_state, response, design_data
    
    # Merge with existing data
    if extracted_params:
        design_data = merge_design_data(design_data, extracted_params)
    
    # === CONSTRAINTS AND VALIDATION ===
    
    # Handle level constraints
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
    
    # === GEOMETRY GENERATION TRIGGER ===
    should_trigger_geometry = False
    geometry_just_completed = False
    
    if (not design_data.get("self_modeling", True) and 
        "geometry" in design_data and 
        all(key in design_data["geometry"] for key in ["typology", "number_of_levels", "width_m", "depth_m"]) and
        not design_data.get("geometry_generated", False)):
        
        should_trigger_geometry = True
        geometry_just_completed = True
        design_data["geometry_generated"] = True  # Mark as generated to avoid repeats
        design_data["trigger_geometry_generation"] = True  # Flag for server
        
        print(f"[CONVERSATION DEBUG] Geometry generation triggered!")
    
    # === DETERMINE NEXT STATE ===
    next_state, next_question = determine_next_missing_parameter(design_data)
    
    # === CREATE RESPONSE ===
    response_parts = []
    
    # Acknowledge extracted parameters
    if extracted_params and not extracted_params.get("wants_ai_suggestion", False):
        acknowledgments = []
        
        # Building type
        if "building_type" in extracted_params:
            acknowledgments.append(f"building type: {extracted_params['building_type']}")
        
        # Geometry parameters
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
        
        # Other parameters
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
            response_parts.append(f"Updated: {', '.join(acknowledgments)}.")
    
    # Handle AI suggestions acknowledgment
    elif extracted_params.get("ai_suggested", False):
        suggestion_items = []
        
        if "geometry" in extracted_params:
            geom = extracted_params["geometry"]
            for key, value in geom.items():
                if key == "typology":
                    suggestion_items.append(f"{value} shape")
                elif key == "number_of_levels":
                    suggestion_items.append(f"{value} levels")
                elif key == "width_m":
                    suggestion_items.append(f"{value}m width")
                elif key == "depth_m":
                    suggestion_items.append(f"{value}m depth")
        
        for key in ["materiality", "climate", "building_type"]:
            if key in extracted_params:
                suggestion_items.append(f"{extracted_params[key]} {key}")
        
        if "wwr" in extracted_params:
            suggestion_items.append(f"{int(extracted_params['wwr']*100)}% windows")
        
        if suggestion_items:
            response_parts.append(f"AI suggested: {', '.join(suggestion_items)}.")
    
    # Add geometry generation notification
    if should_trigger_geometry and geometry_just_completed:
        response_parts.append("🎯 Geometry parameters complete! Generating 3D model...")
    
    # Add validation warning if needed (only at completion)
    if (next_state == "complete" and 
        "geometry" in design_data and 
        all(key in design_data["geometry"] for key in ["typology", "width_m", "depth_m"])):
        
        is_valid, validation_msg = validate_dimensions_for_typology(
            design_data["geometry"]["typology"], 
            design_data["geometry"]["width_m"], 
            design_data["geometry"]["depth_m"]
        )
        if not is_valid:
            response_parts.append(f"⚠️ Note: {validation_msg}. You can adjust if needed.")
    
    # Add next question or completion message
    if next_state == "complete":
        response_parts.append("🎉 All parameters collected! Ready to proceed.")
    else:
        response_parts.append(next_question)
    
    final_response = " ".join(response_parts)
    
    print(f"[CONVERSATION DEBUG] Final state: {next_state}, Response length: {len(final_response)}")
    print(f"[CONVERSATION DEBUG] Geometry trigger: {should_trigger_geometry}")
    
    return next_state, final_response, design_data

# === ENHANCED HELPER FUNCTIONS ===

def handle_real_time_parameter_update(parameter_name, new_value, design_data):
    """Handle real-time updates to specific parameters"""
    
    try:
        print(f"[REAL-TIME UPDATE] {parameter_name} -> {new_value}")
        
        updated_data = design_data.copy()
        
        if parameter_name in ["width", "width_m"]:
            if "geometry" not in updated_data:
                updated_data["geometry"] = {}
            updated_data["geometry"]["width_m"] = round_to_voxel_multiple(float(new_value))
            
        elif parameter_name in ["depth", "depth_m", "length"]:
            if "geometry" not in updated_data:
                updated_data["geometry"] = {}
            updated_data["geometry"]["depth_m"] = round_to_voxel_multiple(float(new_value))
            
        elif parameter_name in ["levels", "number_of_levels"]:
            if "geometry" not in updated_data:
                updated_data["geometry"] = {}
            updated_data["geometry"]["number_of_levels"] = min(int(new_value), MAX_LEVELS)
            
        elif parameter_name == "typology":
            if "geometry" not in updated_data:
                updated_data["geometry"] = {}
            updated_data["geometry"]["typology"] = new_value
            
        elif parameter_name == "materiality":
            updated_data["materiality"] = new_value
            
        elif parameter_name == "climate":
            updated_data["climate"] = new_value
            
        elif parameter_name == "wwr":
            value = float(new_value)
            if value > 1:
                value = value / 100
            updated_data["wwr"] = round(min(value, 0.9), 2)
            
        elif parameter_name == "building_type":
            updated_data["building_type"] = new_value
        
        # Check if this update triggers geometry generation
        if (not updated_data.get("self_modeling", True) and
            parameter_name in ["width", "width_m", "depth", "depth_m", "levels", "number_of_levels", "typology"]):
            
            geometry = updated_data.get("geometry", {})
            if all(key in geometry for key in ["typology", "number_of_levels", "width_m", "depth_m"]):
                updated_data["trigger_geometry_generation"] = True
                updated_data["geometry_generated"] = False  # Allow regeneration
                print(f"[REAL-TIME UPDATE] Triggering geometry regeneration due to {parameter_name} change")
        
        return True, updated_data, f"Updated {parameter_name} to {new_value}"
        
    except Exception as e:
        return False, design_data, f"Error updating {parameter_name}: {str(e)}"

def get_parameter_summary(design_data):
    """Get a formatted summary of current parameters"""
    
    summary_parts = []
    
    if "building_type" in design_data:
        summary_parts.append(f"🏢 Type: {design_data['building_type']}")
    
    if "geometry" in design_data:
        geom = design_data["geometry"]
        geom_parts = []
        
        if "typology" in geom:
            geom_parts.append(f"shape: {geom['typology']}")
        if "number_of_levels" in geom:
            geom_parts.append(f"levels: {geom['number_of_levels']}")
        if "width_m" in geom and "depth_m" in geom:
            geom_parts.append(f"size: {geom['width_m']}×{geom['depth_m']}m")
            
        if geom_parts:
            summary_parts.append(f"📐 Geometry: {', '.join(geom_parts)}")
    
    if "materiality" in design_data:
        summary_parts.append(f"🧱 Material: {design_data['materiality']}")
    
    if "climate" in design_data:
        summary_parts.append(f"🌡️ Climate: {design_data['climate']}")
    
    if "wwr" in design_data:
        summary_parts.append(f"🪟 Windows: {int(design_data['wwr']*100)}%")
    
    modeling_status = "👤 Self-modeling" if design_data.get("self_modeling", True) else "🤖 AI-modeling"
    summary_parts.append(modeling_status)
    
    return " | ".join(summary_parts) if summary_parts else "No parameters set"

# === LEGACY COMPATIBILITY FUNCTIONS ===

def classify_input(user_input):
    """Legacy function - now uses the enhanced extraction"""
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