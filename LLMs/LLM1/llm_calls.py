import json
import os
import time
import re
import traceback
from server.config import client, completion_model

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

def extract_all_parameters_from_input(user_input, current_state="unknown", design_data=None):
    try:
        extracted = {}
        input_lower = user_input.lower().strip()
        
        if not input_lower:
            return extracted
            
        design_data = design_data or {}
        
        print(f"[EXTRACTION DEBUG] Input: '{user_input}'")
        print(f"[EXTRACTION DEBUG] Current state: {current_state}")
        
        if current_state == "wwr" and re.match(r'^\s*\d+\s*(?:percent|%)?\s*$', input_lower):
            wwr_match = re.search(r'(\d+)', input_lower)
            if wwr_match:
                percentage = float(wwr_match.group(1))
                if percentage > 1:
                    percentage = percentage / 100
                extracted["wwr"] = round(min(percentage, 0.9), 2)
                print(f"[EXTRACTION DEBUG] Context-aware WWR: {extracted['wwr']}")
                return extracted
        
        if current_state == "materiality":
            for material in ["brick", "concrete", "earth", "straw", "timber_frame", "timber_mass", "timber", "wood"]:
                if material in input_lower:
                    if material in ["timber", "wood"]:
                        material = "timber_mass"
                    extracted["materiality"] = material
                    print(f"[EXTRACTION DEBUG] Context-aware material: {material}")
                    return extracted
        
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
        
        wwr_patterns = [
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
        
        ml_dict["last_updated"] = time.time()
        
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