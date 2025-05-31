import os
import json
import joblib
import warnings
from datetime import datetime
import re
import shutil

# ============================
# FUNCTION: Predict Outputs
# ============================

_loaded_model = None  # global model cache

def predict_outputs(inputs: dict, model_path: str) -> list:
    """
    Loads model and predicts output from given inputs.

    Args:
        inputs (dict): Input parameter dictionary.
        model_path (str): Path to the .pkl model file.

    Returns:
        list: Model prediction output.
    """
    global _loaded_model

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at: {model_path}")

    if _loaded_model is None:
        _loaded_model = joblib.load(model_path)

    input_order = ["ew_par", "ew_ins", "iw_par", "es_ins", "is_par", "ro_par", "ro_ins", "wwr", "av", "gfa"]
    input_row = [[inputs[k] for k in input_order]]

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        output = _loaded_model.predict(input_row)[0]

    return list(output)

# ============================
# FUNCTION: Save Version JSON
# ============================

def save_version_json(inputs: dict, outputs: list, labels: list, folder: str):
    os.makedirs(folder, exist_ok=True)

    # Load materials decoding
    try:
        with open("Knowledge\materials.json", "r", encoding="utf-8") as mat_file:
            materials_map = json.load(mat_file)
    except Exception as e:
        print(f"⚠️ Could not load materials.json: {e}")
        materials_map = {}

    # Determine next version number
    existing_versions = [f for f in os.listdir(folder) if f.startswith("V") and f.endswith(".json")]
    existing_numbers = [int(f[1:-5]) for f in existing_versions if f[1:-5].isdigit()]
    next_version = max(existing_numbers, default=-1) + 1
    version_name = f"V{next_version}"
    json_path = os.path.join(folder, f"{version_name}.json")

    # Translate input keys
    inputs_raw = {}
    inputs_decoded = {}
    for short_key, value in inputs.items():
        full_key = input_name_map.get(short_key, short_key)

        # If it's a material input
        if full_key in materials_map:
            inputs_raw[full_key] = value
            decoded_value = materials_map[full_key].get(str(value), f"Unknown ({value})")
            inputs_decoded[full_key] = decoded_value
        else:
            # For numeric values like WWR, AV, GFA
            inputs_raw[full_key] = value
            inputs_decoded[full_key] = value

    # Format outputs with readable labels
    formatted_outputs = {
        label.replace("\u00b2", "²"): round(value, 2)
        for label, value in zip(labels, outputs)
    } if outputs else "Prediction failed"

    # Final structure
    version_data = {
        "version": version_name,
        "timestamp": datetime.now().isoformat(),
        "inputs_raw": inputs_raw,
        "inputs_decoded": inputs_decoded,
        "outputs": formatted_outputs
    }

    # Save JSON
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(version_data, f, indent=4, ensure_ascii=False)
        print(f"✅ Saved version file: {json_path}")
    except Exception as e:
        print(f"⚠️ Failed to save JSON version: {e}")


# ============================
# MAIN EXECUTION
# ============================

# Friendly names for JSON output
input_name_map = {
    "ew_par": "Ext.Wall_Partition",
    "ew_ins": "Ext.Wall_Insulation",
    "iw_par": "Int.Wall_Partition",
    "es_ins": "Ext.Slab_Insulation",
    "is_par": "Int.Slab_Partition",
    "ro_par": "Roof_Partition",
    "ro_ins": "Roof_Insulation",
    "wwr": "Window-to-Wall_Ratio",
    "av": "Compactness",
    "gfa": "Gross-Floor-Area"
}


# Input values (customize here)
inputs = {
    "ew_par": 4,
    "ew_ins": 2,
    "iw_par": 1,
    "es_ins": 1,
    "is_par": 0,
    "ro_par": 0,
    "ro_ins": 3,
    "wwr": 0.9,
    "av": 0.9,
    "gfa": 200.0
}

# Output labels
labels = [
    "Energy Intensity - EUI (kWh/m²a)",
    "Cooling Demand (kWh/m²a)",
    "Heating Demand (kWh/m²a)",
    "Operational Carbon (kg CO2e/m²a GFA)",
    "Embodied Carbon A1-A3 (kg CO2e/m²a GFA)",
    "Embodied Carbon A-D (kg CO2e/m²a GFA)",
    "GWP total (kg CO2e/m²a GFA)"
]

# Paths
model_path = r"C:\Users\User\Documents\IAAC\Module03\Encoding\ML\gwp_model_rf_av&gfa.pkl" #GFA+AV-based
json_folder = r"Knowledge\Optioneering"

# Run prediction and save version
try:
    prediction = predict_outputs(inputs, model_path)
    print("\nPrediction Output:")
    for label, value in zip(labels, prediction):
        print(f"{label}: {value:.2f}")
except Exception as e:
    print(f"⚠️ Prediction failed: {e}")
    prediction = []

# Save versioned output
save_version_json(inputs, prediction, labels, json_folder)



# CONFIGURATION
source_folder = 'Knowledge\Optioneering'
destination_folder = 'Knowledge'
destination_filename = 'ml_output.json'  # Set your target filename here

# Regex pattern to extract version like V1, V2, V10, etc.
version_pattern = re.compile(r'V(\d+)', re.IGNORECASE)

def get_version(filename):
    match = version_pattern.search(filename)
    return int(match.group(1)) if match else -1

def find_latest_version_file(folder):
    files = os.listdir(folder)
    versioned_files = [(f, get_version(f)) for f in files if get_version(f) != -1]
    if not versioned_files:
        return None
    # Sort by version number
    latest_file = max(versioned_files, key=lambda x: x[1])[0]
    return os.path.join(folder, latest_file)

def copy_latest_version():
    latest_file_path = find_latest_version_file(source_folder)
    if latest_file_path:
        dest_path = os.path.join(destination_folder, destination_filename)
        shutil.copy2(latest_file_path, dest_path)
        print(f"Copied: {latest_file_path} -> {dest_path}")
    else:
        print("No versioned files found.")

# Run the function
copy_latest_version()
