import json
import os
import time
import re
import traceback
from server.config import client, completion_model

def extract_all_parameters_from_input(user_input, current_state="unknown", design_data=None):
    """Extract parameters from user input - only what's actually mentioned"""
    try:
        extracted = {}
        input_lower = user_input.lower().strip()
        
        if not input_lower:
            return extracted
            
        design_data = design_data or {}
        
        print(f"[EXTRACTION DEBUG] Input: '{user_input}'")
        print(f"[EXTRACTION DEBUG] Current state: {current_state}")
        
        # Context-aware single value extraction
        if current_state == "wwr" and re.match(r'^\s*\d+\s*(?:percent|%)?\s*$', input_lower):
            wwr_match = re.search(r'(\d+)', input_lower)
            if wwr_match:
                percentage = float(wwr_match.group(1))
                if percentage > 1:
                    percentage = percentage / 100
                extracted["wwr"] = round(min(percentage, 0.9), 2)
                print(f"[EXTRACTION DEBUG] Context-aware WWR: {extracted['wwr']}")
                return extracted
        
        # Context-aware material extraction
        if current_state == "materiality":
            for material in ["brick", "concrete", "earth", "straw", "timber_frame", "timber_mass", "timber", "wood"]:
                if material in input_lower:
                    if material in ["timber", "wood"]:
                        material = "timber_mass"
                    extracted["materiality"] = material
                    print(f"[EXTRACTION DEBUG] Context-aware material: {material}")
                    return extracted
        
        # Building levels/stories
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
        
        # Building type
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
        
        # Materials (enhanced patterns)
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
        
        # Climate
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
        
        # WWR (Window-to-Wall Ratio) - enhanced patterns
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
                
                # Handle decimal format
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

def merge_design_data(existing_data, new_data):
    """Merge new extracted data with existing design data"""
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
    """Determine what parameter is still missing"""
    
    # Material selection (first required parameter)
    if "materiality" not in design_data:
        return "materiality", "What material would you like to use? (brick, concrete, timber, earth, straw)"
        
    # Climate context
    if "climate" not in design_data:
        return "climate", "What climate will this building be in? (cold, hot-humid, arid, temperate)"
        
    # Window percentage
    if "wwr" not in design_data:
        return "wwr", "What percentage of windows would you like? (e.g., 30%, 40%)"
    
    # Everything complete
    return "complete", "Great! I have all the basic parameters. Ready to proceed with your design!"

def manage_conversation_state(current_state, user_input, design_data):
    """Main conversation manager - step by step parameter collection"""
    
    print(f"[CONVERSATION DEBUG] State: {current_state}, Input: '{user_input[:50]}...', Current data keys: {list(design_data.keys())}")
    
    # Handle empty input - return original greeting
    if not user_input.strip():
        if not design_data:
            return "initial", "Hello! I'm your design assistant. What would you like to build today?", design_data
        else:
            next_state, next_question = determine_next_missing_parameter(design_data)
            return next_state, next_question, design_data
    
    # Extract parameters from current input
    extracted_params = extract_all_parameters_from_input(user_input, current_state, design_data)
    
    # Merge with existing data
    if extracted_params:
        design_data = merge_design_data(design_data, extracted_params)
    
    # Determine next state and question
    next_state, next_question = determine_next_missing_parameter(design_data)
    
    # Create response
    response_parts = []
    
    # Acknowledge what was extracted
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
    
    # Add next question or completion message
    if next_state == "complete":
        response_parts.append("🎉 Perfect! All basic parameters collected.")
    else:
        response_parts.append(next_question)
    
    final_response = " ".join(response_parts)
    
    print(f"[CONVERSATION DEBUG] Final state: {next_state}, Response: {final_response}")
    
    return next_state, final_response, design_data

def handle_change_or_question(user_input, design_data):
    """Handle changes or questions"""
    try:
        state, reply, updated_data = manage_conversation_state("active", user_input, design_data)
        return state, reply, updated_data
    except Exception as e:
        print(f"Error in handle_change_or_question: {str(e)}")
        return "active", "I'm having trouble with that. Could you try rephrasing?", design_data