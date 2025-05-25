from server.config import *
from llm_calls import *
import json
import os
import shutil
import requests
import datetime

print("\n" + "="*50)
print("🏗️  DESIGN ASSISTANT CLI")
print("="*50)
print("\U0001F44B Hello! I'm your design assistant.")
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

def trigger_geometry_generation(design_data):
    """Trigger geometry generation via Flask server"""
    try:
        print("\n🔄 Sending geometry parameters to generation system...")
        
        response = requests.post(
            "http://127.0.0.1:5000/generate_geometry",
            json={"design_data": design_data},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            params = result.get('parameters', {})
            print(f"✅ Geometry generation triggered:")
            print(f"   Typology: {params.get('typology')}")
            print(f"   Dimensions: {params.get('width_voxels')}×{params.get('depth_voxels')} voxels")
            print(f"   Size: {params.get('width_m')}×{params.get('depth_m')}×{params.get('number_of_levels')*3}m")
            return True
        else:
            print(f"❌ Geometry generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed - is gh_server.py running?")
        return False
    except Exception as e:
        print(f"❌ Error triggering geometry generation: {str(e)}")
        return False

def check_geometry_data():
    """Check if geometry data is available from Grasshopper"""
    try:
        response = requests.get("http://127.0.0.1:5000/get_geometry_data", timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                return True, result
        
        return False, None
        
    except Exception as e:
        print(f"Error checking geometry data: {str(e)}")
        return False, None

def check_server_health():
    """Check if Flask server is running"""
    try:
        response = requests.get("http://127.0.0.1:5000/", timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok':
                return True, "Server is running"
        return False, f"Server responded but with status: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Server not running - start gh_server.py first"
    except requests.exceptions.Timeout:
        return False, "Server timeout - check if server is responsive"
    except Exception as e:
        return False, f"Health check error: {str(e)}"

# Check server status at startup
print("🔍 Checking server status...")
server_ok, server_message = check_server_health()
if server_ok:
    print(f"✅ {server_message}")
else:
    print(f"⚠️  {server_message}")
    print("   Note: You can still use CLI mode, but Grasshopper integration won't work")

# Begin interaction
current_state = "initial"
design_data = {}
iteration_count = 1

print(f"\n[CLI DEBUG] Starting conversation manager...")
print(f"[CLI DEBUG] Initial state: {current_state}")
print(f"[CLI DEBUG] Initial design_data: {design_data}")

# First prompt from the conversation state manager
next_state, prompt, _ = manage_conversation_state(current_state, "", {})
print(f"\n[CLI DEBUG] First prompt generated:")
print(f"[CLI DEBUG] State: {current_state} -> {next_state}")
print(f"[CLI DEBUG] Prompt: {prompt}")

print(f"\n{prompt}")

while True:
    print(f"\n[CLI DEBUG] Current state: {current_state}")
    print(f"[CLI DEBUG] Design data: {design_data}")
    print(f"[CLI DEBUG] Iteration: {iteration_count}")
    
    user_input = input("\n> ")

    if user_input.lower() in ["exit", "quit"]:
        print("\U0001F44B Goodbye!")
        break

    print(f"\n[CLI DEBUG] Processing input: '{user_input}'")
    
    # Process the input based on the current state
    old_state = current_state
    current_state, response, design_data = manage_conversation_state(current_state, user_input, design_data)
    
    print(f"[CLI DEBUG] State transition: {old_state} -> {current_state}")
    print(f"[CLI DEBUG] Response generated: {response[:100]}...")
    
    # Check if we need to trigger geometry generation
    should_generate_geometry = (
        current_state == "complete" and 
        not design_data.get("self_modeling", True) and 
        "geometry" in design_data and 
        "width_m" in design_data.get("geometry", {}) and
        "depth_m" in design_data.get("geometry", {}) and
        "number_of_levels" in design_data.get("geometry", {})
    )
    
    print(f"[CLI DEBUG] Should generate geometry: {should_generate_geometry}")
    
    # Save iteration when we reach "complete" state or make changes to a complete design
    if current_state == "complete":
        # Check if design has all required parameters
        required_params = ["materiality", "climate", "wwr"]
        geometry_params = ["typology", "number_of_levels"]
        
        has_required = all(param in design_data for param in required_params)
        has_geometry = "geometry" in design_data and all(param in design_data["geometry"] for param in geometry_params)
        
        print(f"[CLI DEBUG] Has required params: {has_required}")
        print(f"[CLI DEBUG] Has geometry: {has_geometry}")
        print(f"[CLI DEBUG] Self modeling: {design_data.get('self_modeling', False)}")
        
        if has_required and (design_data.get("self_modeling", False) or has_geometry):
            save_design_iteration(design_data, iteration_count)
            iteration_count += 1
            
        # If this is the first time reaching complete, generate final parameters
        if iteration_count == 2:
            print(f"\n[CLI DEBUG] First completion - generating ML parameters...")
            
            # Generate full parameter set with correct structure
            materiality_params = generate_materiality_json(design_data["materiality"], design_data.get("wwr", 0.3))
            
            # Check if we have geometry data from Grasshopper
            has_geom_data, geom_data = check_geometry_data()
            if has_geom_data:
                materiality_params["gfa"] = geom_data.get('gfa', 200.0)
                materiality_params["av"] = geom_data.get('compactness', 0.5)
                print(f"\n📊 Using geometry data: GFA={geom_data.get('gfa'):.1f}m², Compactness={geom_data.get('compactness'):.3f}")
            
            # Save the final parameters for ML in exact format from diagram
            ml_filename = os.path.join(SESSION_FOLDER, "ml_parameters.json")
            with open(ml_filename, "w") as f:
                json.dump(materiality_params, f, indent=2)
            print(f"\n📊 ML parameters prepared and saved to {ml_filename}")
            
            # If the user isn't self-modeling, trigger geometry generation
            if should_generate_geometry:
                geometry_success = trigger_geometry_generation(design_data)
                if not geometry_success:
                    print("⚠️ Geometry generation failed, but you can still proceed with default values")
    
    # Handle geometry generation trigger during conversation
    elif should_generate_geometry and iteration_count <= 2:
        print("\n🎯 Complete geometry parameters detected!")
        geometry_success = trigger_geometry_generation(design_data)
        if geometry_success:
            print("💡 Your 3D model should now be generating in Grasshopper")
    
    # Print the response
    print(f"\n{response}")
    
    # Show current parameter summary if in complete state
    if current_state == "complete" and design_data:
        print(f"\n📋 Current Parameters:")
        if "building_type" in design_data:
            print(f"   Building: {design_data['building_type']}")
        if "materiality" in design_data:
            print(f"   Material: {design_data['materiality']}")
        if "climate" in design_data:
            print(f"   Climate: {design_data['climate']}")
        if "wwr" in design_data:
            print(f"   WWR: {int(design_data['wwr']*100)}%")
        if "geometry" in design_data:
            geom = design_data["geometry"]
            if "typology" in geom:
                print(f"   Typology: {geom['typology']}")
            if "width_m" in geom and "depth_m" in geom:
                print(f"   Size: {geom['width_m']}×{geom['depth_m']}×{geom.get('number_of_levels', 0)*3}m")
        
        # Show modeling status
        if design_data.get("self_modeling", True):
            print(f"   👤 Self-modeling: You are modeling the geometry")
        else:
            print(f"   🤖 LLM-modeling: I will generate the geometry")
            
        print("   (Type 'exit' to finish)")

print(f"\n[CLI DEBUG] Session ended. Total iterations: {iteration_count-1}")
print(f"📁 All files saved in: {SESSION_FOLDER}")
print("="*50)