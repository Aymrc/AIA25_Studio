from server.config import *
from llm_calls import *
import json
import os
import shutil

print("\n\U0001F44B Hello! I'm your design assistant.")
print("I'll help you define early-stage building parameters for your architectural project.")
print("Let's start by discussing what you'd like to build!\n")

# Folder for storing session iterations
SESSION_FOLDER = "design_iterations"

# Reset folder on start
if os.path.exists(SESSION_FOLDER):
    shutil.rmtree(SESSION_FOLDER)
os.makedirs(SESSION_FOLDER)

# Helper to append iteration files in the session
def save_design_iteration(data, count):
    filename = os.path.join(SESSION_FOLDER, f"iteration_{count}.json")
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\U0001F5C2️ Design parameters saved to {filename}")

# Begin interaction
current_state = "initial"
design_data = {}
iteration_count = 1

# First prompt from the conversation state manager
next_state, prompt, _ = manage_conversation_state(current_state, "", {})
print(f"\n{prompt}")

while True:
    user_input = input("\n> ")

    if user_input.lower() in ["exit", "quit"]:
        print("\U0001F44B Goodbye!")
        break

    # Process the input based on the current state
    current_state, response, design_data = manage_conversation_state(current_state, user_input, design_data)
    
    # Save iteration when we reach "complete" state or make changes to a complete design
    if current_state == "complete":
        # Check if design has all required parameters
        required_params = ["materiality", "climate", "wwr"]
        geometry_params = ["typology", "height", "number_of_levels"]
        
        has_required = all(param in design_data for param in required_params)
        has_geometry = "geometry" in design_data and all(param in design_data["geometry"] for param in geometry_params)
        
        if has_required and (design_data.get("self_modeling", False) or has_geometry):
            save_design_iteration(design_data, iteration_count)
            iteration_count += 1
            
        # If this is the first time reaching complete, generate final parameters
        if iteration_count == 2:
            # Generate full parameter set with correct structure
            materiality_params = generate_materiality_json(design_data["materiality"], design_data.get("wwr", 0.3))
            
            # Save the final parameters for ML in exact format from diagram
            ml_filename = os.path.join(SESSION_FOLDER, "ml_parameters.json")
            with open(ml_filename, "w") as f:
                json.dump(materiality_params, f, indent=2)
            print(f"\n📊 ML parameters prepared and saved to {ml_filename}")
            
            # If the user isn't self-modeling, send to Grasshopper (simulate here)
            if not design_data.get("self_modeling", False):
                print("\n🔄 Sending materiality and WWR parameters to Grasshopper for geometric modeling...")
                # In a real implementation, this would call the Flask endpoint_params = generate_materiality_json(design_data["materiality"], design_data.get("wwr", 0.3))
                final_params = {
                    "parameters": materiality_params,
                    "geometry": design_data.get("geometry", {}),
                    "climate": design_data.get("climate", "temperate"),
                    "building_type": design_data.get("building_type", "generic")
                }
                
                # Save the final parameters for ML
                ml_filename = os.path.join(SESSION_FOLDER, "ml_parameters.json")
                with open(ml_filename, "w") as f:
                    json.dump(final_params, f, indent=2)
                print(f"\n📊 ML parameters prepared and saved to {ml_filename}")
                
                # If the user isn't self-modeling, send to Grasshopper (simulate here)
                if not design_data.get("self_modeling", False):
                    print("\n🔄 Sending parameters to Grasshopper for geometric modeling...")
                    # In a real implementation, this would call the Flask endpoint
    
    # Print the response
    print(f"\n{response}")