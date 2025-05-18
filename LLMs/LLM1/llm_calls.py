import json
import random
from server.config import *

# === CLASSIFICATION CALL FOR RAW TEXT > STRUCTURED PARAMS ===
def classify_input(user_input):
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": """
You are an assistant that extracts architectural design parameters from user input.

Your task is to return a JSON object with the following format. ONLY fill in fields the user explicitly mentions. For anything unclear or missing, just omit the field.

Return exactly this format:

{
  "building_type": "<string>",
  "self_modeling": "<boolean>",
  "materiality": "<brick | concrete | earth | straw | timber_frame | timber_mass>",
  "climate": "<hot-humid | cold | arid | temperate>",
  "wwr": <float>,
  "geometry": {
    "typology": "<courtyard | L-shape | U-shape | block>",
    "height": "<low-rise | mid-rise | high-rise>",
    "number_of_levels": <int>
  }
}

Only output a valid JSON object. Do not add extra text.
"""
            },
            {"role": "user", "content": user_input}
        ]
    )
    
    # Log the raw response for debugging
    print(f"[DEBUG] Raw classification response: {response.choices[0].message.content}")
    
    try:
        # Parse the JSON response
        parsed = json.loads(response.choices[0].message.content)
        return json.dumps(parsed)
    except json.JSONDecodeError:
        # If there's a parsing error, return a minimal JSON structure
        print(f"[ERROR] Failed to parse the LLM response as JSON")
        return json.dumps({"error": "Failed to parse response"})



# === QUERY INTRO ===
def query_intro():
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Introduce yourself as a design assistant. Explain that you will help collect "
                    "basic architectural parameters such as materiality, climate, WWR, and geometry, "
                    "to feed a generative ML prediction engine."
                )
            }
        ]
    )
    return response.choices[0].message.content.strip()

# === STRUCTURED PARSING ===
def collect_design_parameters(user_input, messages):
    try:
        raw = classify_input(user_input)
        return json.loads(raw)
    except Exception as e:
        return {}

# === CONVERSATION STATE MANAGER ===
def manage_conversation_state(current_state, user_input, design_data):
    """
    Manages the conversation flow based on the current state and user input
    Returns: (new_state, response, updated_design_data)
    """
    print(f"[DEBUG] Processing state '{current_state}' with input: '{user_input}'")
    
    # Check for uncertainty in user input
    is_uncertain = any(phrase in user_input.lower() for phrase in 
                      ["not sure", "don't know", "random", "uncertain", "any", "whatever", "you choose", 
                       "you decide", "suggest", "your choice", "up to you", "don't care"])
    
    # Extract building type from input if we're in initial state
    if current_state == "initial" or current_state == "building_type":
        # Check for residential building mentions
        is_residential = any(term in user_input.lower() for term in 
                            ["residential", "apartment", "housing", "house", "home", "flat", "condo", "storey"])
        
        # Check for specific building mentions
        building_found = any(term in user_input.lower() for term in 
                            ["residential", "office", "commercial", "mixed-use", "museum", "hospital", 
                             "school", "hotel", "tower", "housing"])
        
        # If we found a building type, store it
        if is_residential or building_found:
            design_data["building_type"] = user_input.strip()
            print(f"[DEBUG] Detected building type: {design_data['building_type']}")
            
            # Extract levels if mentioned
            if "storey" in user_input.lower() or "story" in user_input.lower() or "level" in user_input.lower() or "floor" in user_input.lower():
                try:
                    # Try to extract numbers
                    import re
                    numbers = re.findall(r'\d+', user_input)
                    if numbers:
                        num_levels = int(numbers[0])
                        if "geometry" not in design_data:
                            design_data["geometry"] = {}
                        design_data["geometry"]["number_of_levels"] = num_levels
                        
                        # Determine height category
                        if num_levels <= 3:
                            design_data["geometry"]["height"] = "low-rise"
                        elif num_levels <= 12:
                            design_data["geometry"]["height"] = "mid-rise"
                        else:
                            design_data["geometry"]["height"] = "high-rise"
                        
                        print(f"[DEBUG] Detected levels: {num_levels}, height: {design_data['geometry']['height']}")
                except Exception as e:
                    print(f"[DEBUG] Error parsing levels: {str(e)}")
    
    # Now handle state transitions as before
    if current_state == "initial":
        # First, ask what they want to build
        if is_uncertain:
            # Offer a random suggestion
            building_types = ["residential apartment building", "office tower", "cultural center", 
                              "mixed-use development", "educational facility", "boutique hotel"]
            suggestion = random.choice(building_types)
            design_data["building_type"] = suggestion
            return "modeling_preference", f"I'll suggest a {suggestion}. Will you be modeling the geometry directly, or would you like me to model it for you based on your description?", design_data
        elif "building_type" in design_data:
            # If we've already extracted a building type, move to the next state
            return "modeling_preference", f"Great! You want to build {design_data['building_type']}. Will you be modeling the geometry directly, or would you like me to model it for you based on your description?", design_data
        else:
            return "building_type", "What would you like to build? (For example: a residential building, an office tower, etc.)", design_data
    
    elif current_state == "building_type":
        # Store their building type and ask about modeling
        if "building_type" not in design_data:
            design_data["building_type"] = user_input
        return "modeling_preference", "Will you be modeling the geometry directly, or would you like me to model it for you based on your description?", design_data
    
    elif current_state == "modeling_preference":
        # Process their modeling preference
        if is_uncertain:
            # Default to LLM modeling if uncertain
            design_data["self_modeling"] = False
            return "typology", "I'll model it for you. What typology would you prefer? Options are: courtyard, L-shape, U-shape, or block. (Or say 'not sure' for a suggestion)", design_data
        elif any(word in user_input.lower() for word in ["i will", "myself", "direct", "i'll model", "i am"]):
            design_data["self_modeling"] = True
            return "material", "Great! What material would you like to use? Options include brick, concrete, earth, straw, timber frame, or timber mass. (Or say 'not sure' for a suggestion)", design_data
        else:
            design_data["self_modeling"] = False
            return "typology", "What typology would you prefer? Options are: courtyard, L-shape, U-shape, or block. (Or say 'not sure' for a suggestion)", design_data
    
    elif current_state == "typology":
        # Store typology and ask about levels
        if "geometry" not in design_data:
            design_data["geometry"] = {}
        
        if is_uncertain:
            # Suggest a random typology
            typologies = ["courtyard", "L-shape", "U-shape", "block"]
            suggested_typology = random.choice(typologies)
            design_data["geometry"]["typology"] = suggested_typology
            return "levels", f"I'll suggest a {suggested_typology} typology. How many levels would you like the building to have? (Or say 'not sure' for a suggestion)", design_data
        
        # Extract typology from input
        if "l" in user_input.lower() and "shape" in user_input.lower():
            design_data["geometry"]["typology"] = "L-shape"
        elif "u" in user_input.lower() and "shape" in user_input.lower():
            design_data["geometry"]["typology"] = "U-shape"
        elif "court" in user_input.lower():
            design_data["geometry"]["typology"] = "courtyard"
        elif "block" in user_input.lower():
            design_data["geometry"]["typology"] = "block"
        else:
            # Default if unclear
            design_data["geometry"]["typology"] = user_input
            
        # If we already detected levels, skip to material
        if "number_of_levels" in design_data.get("geometry", {}):
            return "material", "What material would you like to use? Options include brick, concrete, earth, straw, timber frame, or timber mass. (Or say 'not sure' for a suggestion)", design_data
        else:
            return "levels", "How many levels would you like the building to have? (Or say 'not sure' for a suggestion)", design_data
    
    elif current_state == "levels":
        # Store number of levels and ask about material
        if "geometry" not in design_data:
            design_data["geometry"] = {}
            
        if is_uncertain:
            # Suggest a random number of levels based on building type
            building_type = design_data.get("building_type", "").lower()
            
            if "house" in building_type or "residential" in building_type and "tower" not in building_type:
                num_levels = random.randint(1, 4)  # Small residential
            elif "office" in building_type or "tower" in building_type or "high" in building_type:
                num_levels = random.randint(8, 20)  # Office tower
            else:
                num_levels = random.randint(3, 8)  # Default mid-rise
                
            design_data["geometry"]["number_of_levels"] = num_levels
            
            # Determine height category based on levels
            if num_levels <= 3:
                design_data["geometry"]["height"] = "low-rise"
            elif num_levels <= 12:
                design_data["geometry"]["height"] = "mid-rise"
            else:
                design_data["geometry"]["height"] = "high-rise"
                
            return "material", f"I'll suggest a {num_levels}-level building. What material would you like to use? Options include brick, concrete, earth, straw, timber frame, or timber mass. (Or say 'not sure' for a suggestion)", design_data
        
        # Try to extract a number
        try:
            import re
            numbers = re.findall(r'\d+', user_input)
            if numbers:
                num_levels = int(numbers[0])
                design_data["geometry"]["number_of_levels"] = num_levels
                
                # Determine height category based on levels
                if num_levels <= 3:
                    design_data["geometry"]["height"] = "low-rise"
                elif num_levels <= 12:
                    design_data["geometry"]["height"] = "mid-rise"
                else:
                    design_data["geometry"]["height"] = "high-rise"
                    
                return "material", "What material would you like to use? Options include brick, concrete, earth, straw, timber frame, or timber mass. (Or say 'not sure' for a suggestion)", design_data
            else:
                return "levels", "I didn't catch a number. How many levels would you like the building to have? Please provide a number or say 'not sure' for a suggestion.", design_data
        except:
            # If we can't parse a number, ask again
            return "levels", "I'm sorry, I couldn't understand the number of levels. Please provide a number or say 'not sure' for a suggestion.", design_data
        
    elif current_state == "material":
        # Store material choice and ask about climate
        if is_uncertain:
            # Suggest a random material based on building type and height
            materials = ["brick", "concrete", "earth", "straw", "timber_frame", "timber_mass"]
            building_type = design_data.get("building_type", "").lower()
            height = design_data.get("geometry", {}).get("height", "")
            
            # For high-rise buildings, prefer concrete or timber mass
            if height == "high-rise":
                suggested_material = random.choice(["concrete", "timber_mass"])
            # For low-rise residential, prefer more variety
            elif height == "low-rise" and ("house" in building_type or "residential" in building_type):
                suggested_material = random.choice(materials)
            # Default to common materials for typical buildings
            else:
                suggested_material = random.choice(["brick", "concrete", "timber_frame"])
                
            design_data["materiality"] = suggested_material
            return "climate", f"I'll suggest {suggested_material} as your main material. What climate is the building designed for? (hot-humid, cold, arid, or temperate) (Or say 'not sure' for a suggestion)", design_data
        
        lower_input = user_input.lower()
        if "brick" in lower_input:
            design_data["materiality"] = "brick"
        elif "concrete" in lower_input:
            design_data["materiality"] = "concrete"
        elif "earth" in lower_input:
            design_data["materiality"] = "earth"
        elif "straw" in lower_input:
            design_data["materiality"] = "straw"
        elif "timber frame" in lower_input or ("frame" in lower_input and "timber" in lower_input):
            design_data["materiality"] = "timber_frame"
        elif "timber mass" in lower_input or ("mass" in lower_input and "timber" in lower_input):
            design_data["materiality"] = "timber_mass"
        else:
            # If unclear, ask for clarification
            return "material", "I didn't catch that. Please specify one of: brick, concrete, earth, straw, timber frame, or timber mass. Or say 'not sure' for a suggestion.", design_data
            
        return "climate", "What climate is the building designed for? (hot-humid, cold, arid, or temperate) (Or say 'not sure' for a suggestion)", design_data
    
    elif current_state == "climate":
        # Store climate and ask about WWR
        if is_uncertain:
            # Suggest climate based on general patterns
            climates = ["hot-humid", "cold", "arid", "temperate"]
            suggested_climate = random.choice(climates)
            design_data["climate"] = suggested_climate
            return "wwr", f"I'll suggest a {suggested_climate} climate. What window-to-wall ratio (WWR) would you like? This is the percentage of the facade that will be glazed. You can give a percentage or just say 'not sure'.", design_data
            
        lower_input = user_input.lower()
        if "hot" in lower_input or "humid" in lower_input:
            design_data["climate"] = "hot-humid"
        elif "cold" in lower_input:
            design_data["climate"] = "cold"
        elif "arid" in lower_input or "dry" in lower_input:
            design_data["climate"] = "arid"
        elif "temperate" in lower_input or "mild" in lower_input:
            design_data["climate"] = "temperate"
        else:
            # If unclear, ask for clarification
            return "climate", "I didn't catch that. Please specify one of: hot-humid, cold, arid, or temperate. Or say 'not sure' for a suggestion.", design_data
            
        return "wwr", "What window-to-wall ratio (WWR) would you like? This is the percentage of the facade that will be glazed. You can give a percentage or just say 'not sure'.", design_data
    
    elif current_state == "wwr":
        # Process WWR value
        if is_uncertain:
            # Generate a reasonable random WWR based on climate and building type
            climate = design_data.get("climate", "temperate")
            
            # Adjust WWR ranges based on climate for energy efficiency
            if climate == "hot-humid":
                wwr = round(random.uniform(0.2, 0.4), 2)  # Lower WWR for hot climates
            elif climate == "cold":
                wwr = round(random.uniform(0.3, 0.5), 2)  # Medium-high WWR for cold (solar gain)
            elif climate == "arid":
                wwr = round(random.uniform(0.15, 0.35), 2)  # Lower WWR for arid climates
            else:  # temperate
                wwr = round(random.uniform(0.3, 0.6), 2)  # Higher range for temperate
                
            design_data["wwr"] = wwr
            return "complete", f"I've set the WWR to {int(wwr*100)}%. Your design parameters are now complete! You can ask me questions about the design or request changes.", design_data
        else:
            # Try to extract a percentage
            try:
                import re
                numbers = re.findall(r'\d+(?:\.\d+)?', user_input)
                if numbers:
                    percentage = float(numbers[0])
                    
                    # Convert percentage to decimal if needed
                    if percentage > 1:
                        percentage = percentage / 100
                    
                    design_data["wwr"] = round(percentage, 2)
                    return "complete", "Thank you! Your design parameters are now complete. You can ask me questions about the design or request changes.", design_data
                else:
                    return "wwr", "I couldn't find a number in your response. Please provide a percentage (like 30%) or say 'not sure' if you want me to choose for you.", design_data
            except:
                return "wwr", "I couldn't understand that value. Please provide a percentage (like 30%) or say 'not sure' if you want me to choose for you.", design_data
    
    elif current_state == "complete":
        # Now in Q&A mode - check if they want to change something
        return handle_change_or_question(user_input, design_data)
        
    else:
        # Default case - move to Q&A
        return "complete", "I'm not sure what to do next. Your design parameters are complete. Feel free to ask questions or request changes.", design_data
    if current_state == "initial":
        # First, ask what they want to build
        if is_uncertain:
            # Offer a random suggestion
            building_types = ["residential apartment building", "office tower", "cultural center", 
                              "mixed-use development", "educational facility", "boutique hotel"]
            suggestion = random.choice(building_types)
            design_data["building_type"] = suggestion
            return "modeling_preference", f"I'll suggest a {suggestion}. Will you be modeling the geometry directly, or would you like me to model it for you based on your description?", design_data
        elif "building_type" in design_data:
            # If we've already extracted a building type, move to the next state
            return "modeling_preference", f"Great! You want to build {design_data['building_type']}. Will you be modeling the geometry directly, or would you like me to model it for you based on your description?", design_data
        else:
            return "building_type", "What would you like to build? (For example: a residential building, an office tower, etc.)", design_data
    
    elif current_state == "building_type":
        # Store their building type and ask about modeling
        if "building_type" not in design_data:
            design_data["building_type"] = user_input
        return "modeling_preference", "Will you be modeling the geometry directly, or would you like me to model it for you based on your description?", design_data
    
    elif current_state == "modeling_preference":
        # Process their modeling preference
        if is_uncertain:
            # Default to LLM modeling if uncertain
            design_data["self_modeling"] = False
            return "typology", "I'll model it for you. What typology would you prefer? Options are: courtyard, L-shape, U-shape, or block. (Or say 'not sure' for a suggestion)", design_data
        elif any(word in user_input.lower() for word in ["i will", "myself", "direct", "i'll model", "i am"]):
            design_data["self_modeling"] = True
            return "material", "Great! What material would you like to use? Options include brick, concrete, earth, straw, timber frame, or timber mass. (Or say 'not sure' for a suggestion)", design_data
        else:
            design_data["self_modeling"] = False
            return "typology", "What typology would you prefer? Options are: courtyard, L-shape, U-shape, or block. (Or say 'not sure' for a suggestion)", design_data
    
    elif current_state == "typology":
        # Store typology and ask about levels
        if "geometry" not in design_data:
            design_data["geometry"] = {}
        
        if is_uncertain:
            # Suggest a random typology
            typologies = ["courtyard", "L-shape", "U-shape", "block"]
            suggested_typology = random.choice(typologies)
            design_data["geometry"]["typology"] = suggested_typology
            return "levels", f"I'll suggest a {suggested_typology} typology. How many levels would you like the building to have? (Or say 'not sure' for a suggestion)", design_data
        
        # Extract typology from input
        if "l" in user_input.lower() and "shape" in user_input.lower():
            design_data["geometry"]["typology"] = "L-shape"
        elif "u" in user_input.lower() and "shape" in user_input.lower():
            design_data["geometry"]["typology"] = "U-shape"
        elif "court" in user_input.lower():
            design_data["geometry"]["typology"] = "courtyard"
        elif "block" in user_input.lower():
            design_data["geometry"]["typology"] = "block"
        else:
            # Default if unclear
            design_data["geometry"]["typology"] = user_input
            
        # If we already detected levels, skip to material
        if "number_of_levels" in design_data.get("geometry", {}):
            return "material", "What material would you like to use? Options include brick, concrete, earth, straw, timber frame, or timber mass. (Or say 'not sure' for a suggestion)", design_data
        else:
            return "levels", "How many levels would you like the building to have? (Or say 'not sure' for a suggestion)", design_data
    
    elif current_state == "levels":
        # Store number of levels and ask about material
        if "geometry" not in design_data:
            design_data["geometry"] = {}
            
        if is_uncertain:
            # Suggest a random number of levels based on building type
            building_type = design_data.get("building_type", "").lower()
            
            if "house" in building_type or "residential" in building_type and "tower" not in building_type:
                num_levels = random.randint(1, 4)  # Small residential
            elif "office" in building_type or "tower" in building_type or "high" in building_type:
                num_levels = random.randint(8, 20)  # Office tower
            else:
                num_levels = random.randint(3, 8)  # Default mid-rise
                
            design_data["geometry"]["number_of_levels"] = num_levels
            
            # Determine height category based on levels
            if num_levels <= 3:
                design_data["geometry"]["height"] = "low-rise"
            elif num_levels <= 12:
                design_data["geometry"]["height"] = "mid-rise"
            else:
                design_data["geometry"]["height"] = "high-rise"
                
            return "material", f"I'll suggest a {num_levels}-level building. What material would you like to use? Options include brick, concrete, earth, straw, timber frame, or timber mass. (Or say 'not sure' for a suggestion)", design_data
        
        # Try to extract a number
        try:
            import re
            numbers = re.findall(r'\d+', user_input)
            if numbers:
                num_levels = int(numbers[0])
                design_data["geometry"]["number_of_levels"] = num_levels
                
                # Determine height category based on levels
                if num_levels <= 3:
                    design_data["geometry"]["height"] = "low-rise"
                elif num_levels <= 12:
                    design_data["geometry"]["height"] = "mid-rise"
                else:
                    design_data["geometry"]["height"] = "high-rise"
                    
                return "material", "What material would you like to use? Options include brick, concrete, earth, straw, timber frame, or timber mass. (Or say 'not sure' for a suggestion)", design_data
            else:
                return "levels", "I didn't catch a number. How many levels would you like the building to have? Please provide a number or say 'not sure' for a suggestion.", design_data
        except:
            # If we can't parse a number, ask again
            return "levels", "I'm sorry, I couldn't understand the number of levels. Please provide a number or say 'not sure' for a suggestion.", design_data
        
    elif current_state == "material":
        # Store material choice and ask about climate
        if is_uncertain:
            # Suggest a random material based on building type and height
            materials = ["brick", "concrete", "earth", "straw", "timber_frame", "timber_mass"]
            building_type = design_data.get("building_type", "").lower()
            height = design_data.get("geometry", {}).get("height", "")
            
            # For high-rise buildings, prefer concrete or timber mass
            if height == "high-rise":
                suggested_material = random.choice(["concrete", "timber_mass"])
            # For low-rise residential, prefer more variety
            elif height == "low-rise" and ("house" in building_type or "residential" in building_type):
                suggested_material = random.choice(materials)
            # Default to common materials for typical buildings
            else:
                suggested_material = random.choice(["brick", "concrete", "timber_frame"])
                
            design_data["materiality"] = suggested_material
            return "climate", f"I'll suggest {suggested_material} as your main material. What climate is the building designed for? (hot-humid, cold, arid, or temperate) (Or say 'not sure' for a suggestion)", design_data
        
        lower_input = user_input.lower()
        if "brick" in lower_input:
            design_data["materiality"] = "brick"
        elif "concrete" in lower_input:
            design_data["materiality"] = "concrete"
        elif "earth" in lower_input:
            design_data["materiality"] = "earth"
        elif "straw" in lower_input:
            design_data["materiality"] = "straw"
        elif "timber frame" in lower_input or ("frame" in lower_input and "timber" in lower_input):
            design_data["materiality"] = "timber_frame"
        elif "timber mass" in lower_input or ("mass" in lower_input and "timber" in lower_input):
            design_data["materiality"] = "timber_mass"
        else:
            # If unclear, ask for clarification
            return "material", "I didn't catch that. Please specify one of: brick, concrete, earth, straw, timber frame, or timber mass. Or say 'not sure' for a suggestion.", design_data
            
        return "climate", "What climate is the building designed for? (hot-humid, cold, arid, or temperate) (Or say 'not sure' for a suggestion)", design_data
    
    elif current_state == "climate":
        # Store climate and ask about WWR
        if is_uncertain:
            # Suggest climate based on general patterns
            climates = ["hot-humid", "cold", "arid", "temperate"]
            suggested_climate = random.choice(climates)
            design_data["climate"] = suggested_climate
            return "wwr", f"I'll suggest a {suggested_climate} climate. What window-to-wall ratio (WWR) would you like? This is the percentage of the facade that will be glazed. You can give a percentage or just say 'not sure'.", design_data
            
        lower_input = user_input.lower()
        if "hot" in lower_input or "humid" in lower_input:
            design_data["climate"] = "hot-humid"
        elif "cold" in lower_input:
            design_data["climate"] = "cold"
        elif "arid" in lower_input or "dry" in lower_input:
            design_data["climate"] = "arid"
        elif "temperate" in lower_input or "mild" in lower_input:
            design_data["climate"] = "temperate"
        else:
            # If unclear, ask for clarification
            return "climate", "I didn't catch that. Please specify one of: hot-humid, cold, arid, or temperate. Or say 'not sure' for a suggestion.", design_data
            
        return "wwr", "What window-to-wall ratio (WWR) would you like? This is the percentage of the facade that will be glazed. You can give a percentage or just say 'not sure'.", design_data
    
    elif current_state == "wwr":
        # Process WWR value
        if is_uncertain:
            # Generate a reasonable random WWR based on climate and building type
            climate = design_data.get("climate", "temperate")
            
            # Adjust WWR ranges based on climate for energy efficiency
            if climate == "hot-humid":
                wwr = round(random.uniform(0.2, 0.4), 2)  # Lower WWR for hot climates
            elif climate == "cold":
                wwr = round(random.uniform(0.3, 0.5), 2)  # Medium-high WWR for cold (solar gain)
            elif climate == "arid":
                wwr = round(random.uniform(0.15, 0.35), 2)  # Lower WWR for arid climates
            else:  # temperate
                wwr = round(random.uniform(0.3, 0.6), 2)  # Higher range for temperate
                
            design_data["wwr"] = wwr
            return "complete", f"I've set the WWR to {int(wwr*100)}%. Your design parameters are now complete! You can ask me questions about the design or request changes.", design_data
        else:
            # Try to extract a percentage
            try:
                import re
                numbers = re.findall(r'\d+(?:\.\d+)?', user_input)
                if numbers:
                    percentage = float(numbers[0])
                    
                    # Convert percentage to decimal if needed
                    if percentage > 1:
                        percentage = percentage / 100
                    
                    design_data["wwr"] = round(percentage, 2)
                    return "complete", "Thank you! Your design parameters are now complete. You can ask me questions about the design or request changes.", design_data
                else:
                    return "wwr", "I couldn't find a number in your response. Please provide a percentage (like 30%) or say 'not sure' if you want me to choose for you.", design_data
            except:
                return "wwr", "I couldn't understand that value. Please provide a percentage (like 30%) or say 'not sure' if you want me to choose for you.", design_data
    
    elif current_state == "complete":
        # Now in Q&A mode - check if they want to change something
        return handle_change_or_question(user_input, design_data)
        
    else:
        # Default case - move to Q&A
        return "complete", "I'm not sure what to do next. Your design parameters are complete. Feel free to ask questions or request changes.", design_data
    if current_state == "initial":
        # First, ask what they want to build
        return "building_type", "What would you like to build? (For example: a residential building, an office tower, etc.)", design_data
    
    elif current_state == "building_type":
        # Store their building type and ask about modeling
        design_data["building_type"] = user_input
        return "modeling_preference", "Will you be modeling the geometry directly, or would you like me to model it for you based on your description?", design_data
    
    elif current_state == "modeling_preference":
        # Process their modeling preference
        if any(word in user_input.lower() for word in ["i will", "myself", "direct", "i'll model", "i am"]):
            design_data["self_modeling"] = True
            return "material", "Great! What material would you like to use? Options include brick, concrete, earth, straw, timber frame, or timber mass.", design_data
        else:
            design_data["self_modeling"] = False
            return "typology", "What typology would you prefer? Options are: courtyard, L-shape, U-shape, or block.", design_data
    
    elif current_state == "typology":
        # Store typology and ask about levels
        if "geometry" not in design_data:
            design_data["geometry"] = {}
        
        # Extract typology from input
        if "l" in user_input.lower() and "shape" in user_input.lower():
            design_data["geometry"]["typology"] = "L-shape"
        elif "u" in user_input.lower() and "shape" in user_input.lower():
            design_data["geometry"]["typology"] = "U-shape"
        elif "court" in user_input.lower():
            design_data["geometry"]["typology"] = "courtyard"
        elif "block" in user_input.lower():
            design_data["geometry"]["typology"] = "block"
        else:
            # Default if unclear
            design_data["geometry"]["typology"] = user_input
            
        return "levels", "How many levels would you like the building to have?", design_data
    
    elif current_state == "levels":
        # Store number of levels and ask about material
        try:
            num_levels = int(''.join(filter(str.isdigit, user_input)))
            if "geometry" not in design_data:
                design_data["geometry"] = {}
            design_data["geometry"]["number_of_levels"] = num_levels
            
            # Determine height category based on levels
            if num_levels <= 3:
                design_data["geometry"]["height"] = "low-rise"
            elif num_levels <= 12:
                design_data["geometry"]["height"] = "mid-rise"
            else:
                design_data["geometry"]["height"] = "high-rise"
        except:
            # If we can't parse a number, ask again
            return "levels", "I'm sorry, I couldn't understand the number of levels. Please provide a number.", design_data
        
        return "material", "What material would you like to use? Options include brick, concrete, earth, straw, timber frame, or timber mass.", design_data
        
    elif current_state == "material":
        # Store material choice and ask about climate
        lower_input = user_input.lower()
        if "brick" in lower_input:
            design_data["materiality"] = "brick"
        elif "concrete" in lower_input:
            design_data["materiality"] = "concrete"
        elif "earth" in lower_input:
            design_data["materiality"] = "earth"
        elif "straw" in lower_input:
            design_data["materiality"] = "straw"
        elif "timber frame" in lower_input or "frame" in lower_input:
            design_data["materiality"] = "timber_frame"
        elif "timber mass" in lower_input or "mass" in lower_input:
            design_data["materiality"] = "timber_mass"
        else:
            # If unclear, ask for clarification
            return "material", "I didn't catch that. Please specify one of: brick, concrete, earth, straw, timber frame, or timber mass.", design_data
            
        return "climate", "What climate is the building designed for? (hot-humid, cold, arid, or temperate)", design_data
    
    elif current_state == "climate":
        # Store climate and ask about WWR
        lower_input = user_input.lower()
        if "hot" in lower_input or "humid" in lower_input:
            design_data["climate"] = "hot-humid"
        elif "cold" in lower_input:
            design_data["climate"] = "cold"
        elif "arid" in lower_input or "dry" in lower_input:
            design_data["climate"] = "arid"
        elif "temperate" in lower_input or "mild" in lower_input:
            design_data["climate"] = "temperate"
        else:
            # If unclear, ask for clarification
            return "climate", "I didn't catch that. Please specify one of: hot-humid, cold, arid, or temperate.", design_data
            
        return "wwr", "What window-to-wall ratio (WWR) would you like? This is the percentage of the facade that will be glazed. You can give a percentage or just say 'not sure'.", design_data
    
    elif current_state == "wwr":
        # Process WWR value
        if "not sure" in user_input.lower() or "random" in user_input.lower():
            # Generate a reasonable random WWR
            wwr = round(random.uniform(0.2, 0.6), 2)
            design_data["wwr"] = wwr
            return "complete", f"I've set the WWR to {wwr*100}% for you. Your design parameters are now complete!", design_data
        else:
            # Try to extract a percentage
            try:
                # Remove non-numeric characters except decimal points
                numeric_str = ''.join(c for c in user_input if c.isdigit() or c == '.')
                percentage = float(numeric_str)
                
                # Convert percentage to decimal if needed
                if percentage > 1:
                    percentage = percentage / 100
                
                design_data["wwr"] = round(percentage, 2)
                return "complete", "Thank you! Your design parameters are now complete.", design_data
            except:
                return "wwr", "I couldn't understand that value. Please provide a percentage (like 30%) or say 'not sure' if you want me to choose for you.", design_data
    
    elif current_state == "complete":
        # Now in Q&A mode - check if they want to change something
        return handle_change_or_question(user_input, design_data)
        
    else:
        # Default case - move to Q&A
        return "complete", "I'm not sure what to do next. Your design parameters are complete. Feel free to ask questions or request changes.", design_data

def handle_change_or_question(user_input, design_data):
    """Handle changes or questions in the Q&A phase"""
    lowered = user_input.lower()
    
    # Check for change requests
    change_keywords = ["change", "replace", "switch", "update", "make it", "modify", "set", "turn into"]
    if any(kw in lowered for kw in change_keywords):
        result = suggest_change(user_input, design_data)
        try:
            change = json.loads(result)
            target = change["target"]
            new_value = change["new_value"]
            
            # Update the design data based on the target
            if "." in target:
                # Handle nested properties
                parts = target.split(".")
                if len(parts) == 2:
                    if parts[0] not in design_data:
                        design_data[parts[0]] = {}
                    design_data[parts[0]][parts[1]] = new_value
            else:
                # Handle top-level properties
                design_data[target] = new_value
                
            return "complete", f"Updated {target} to {new_value}. {change.get('rationale', '')}", design_data
        except Exception as e:
            return "complete", f"I had trouble processing that change. Could you be more specific about what you want to change?", design_data
    
    # Check for improvement requests
    improve_keywords = ["improve", "reduce", "maximize", "minimize", "optimize", "should i", "could i", "recommend", "how can i"]
    if any(kw in lowered for kw in improve_keywords):
        suggestion = suggest_improvements(user_input, design_data)
        return "complete", suggestion, design_data
    
    # Default to general Q&A
    reply = answer_user_query(user_input, design_data)
    return "complete", reply, design_data

# === CHANGE SUGGESTIONS ===
def suggest_change(user_prompt, design_data):
    design_data_json = json.dumps(design_data)
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": f"""
You are a structured assistant. The user wants to change something in this building design:

{design_data_json}

Respond ONLY with a JSON object:
{{
  "action": "update",
  "target": "<parameter_to_change>",
  "new_value": "<desired_value>",
  "rationale": "<why it's a good change>"
}}
"""
            },
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content

# === IMPROVEMENT SUGGESTIONS ===
def suggest_improvements(user_prompt, design_data):
    design_data_json = json.dumps(design_data)
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": f"""
Suggest 1–2 creative improvements based on this building design (JSON below).
Be specific and helpful. Avoid boilerplate or obvious suggestions.

{design_data_json}
"""
            },
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content

# === GENERAL Q&A ===
def answer_user_query(user_prompt, design_data):
    design_data_json = json.dumps(design_data)
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": f"""
Answer the user's design question using the following data:

{design_data_json}

Keep it friendly and informative. Do NOT mention legal restrictions, codes, or impossibilities.
If information is missing, kindly ask the user to provide it.
"""
            },
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content

# === MATERIAL TO JSON MAP ===
def map_material_to_json_values(material):
    """
    Maps the selected material to corresponding JSON parameter values
    Returns a dictionary of parameter values based on the material choice
    """
    # Default values - using exact structure from diagram
    defaults = {
        "ew_par": 0,  # Default to brick
        "ew_ins": 0,  # Default to cellulose
        "iw_par": 0,  # Default to brick
        "es_ins": 1,  # Default to cork
        "is_par": 0,  # Default to concrete
        "ro_par": 0,  # Default to concrete
        "ro_ins": 0,  # Default to cellulose
    }
    
    # Material mappings from image 1
    # Envelope Wall Partition (ew_par)
    ew_par_map = {
        "brick": 0,
        "concrete": 1,
        "earth": 2,
        "straw": 3,
        "timber_frame": 4,
        "timber_mass": 5
    }
    
    # Envelope Wall Insulation (ew_ins)
    ew_ins_map = {
        "cellulose": 0,
        "cork": 1,
        "eps": 2,
        "glass_wool": 3,
        "mineral_wool": 4,
        "wood_fiber": 5
    }
    
    # Interior Wall Partition (iw_par) - same as ew_par
    iw_par_map = ew_par_map
    
    # External Slab Insulation (es_ins)
    es_ins_map = {
        "expanded_glass": 0,
        "xps": 1
    }
    
    # Internal Slab Partition (is_par)
    is_par_map = {
        "concrete": 0,
        "timber_frame": 1,
        "timber_mass": 2
    }
    
    # Roof Partition (ro_par) - same as is_par
    ro_par_map = is_par_map
    
    # Roof Insulation (ro_ins)
    ro_ins_map = {
        "cellulose": 0,
        "cork": 1,
        "eps": 2,
        "expanded_glass": 3,
        "glass_wool": 4,
        "mineral_wool": 5,
        "wood_fiber": 6,
        "xps": 7
    }
    
    # Update values based on material selection
    if material in ew_par_map:
        # Set envelope wall partition to selected material
        defaults["ew_par"] = ew_par_map[material]
        
        # Set interior wall partition to match exterior
        defaults["iw_par"] = ew_par_map[material]
        
        # Set appropriate structural material based on selection
        if material in ["timber_frame", "timber_mass"]:
            # For timber-based exteriors, use timber for structure and roof
            if material == "timber_frame":
                defaults["is_par"] = is_par_map["timber_frame"]
                defaults["ro_par"] = ro_par_map["timber_frame"]
            else:  # timber_mass
                defaults["is_par"] = is_par_map["timber_mass"]
                defaults["ro_par"] = ro_par_map["timber_mass"]
        else:
            # For other materials, use concrete for structure
            defaults["is_par"] = is_par_map["concrete"]
            defaults["ro_par"] = ro_par_map["concrete"]
        
        # Set default insulation values - could be randomized or based on climate later
        defaults["ew_ins"] = ew_ins_map["cellulose"]  # Default insulation
        defaults["es_ins"] = es_ins_map["xps"]        # Default external slab insulation
        defaults["ro_ins"] = ro_ins_map["cellulose"]  # Default roof insulation
    
    return defaults

# Function to generate a materiality parameters JSON object
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