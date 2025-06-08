import os
import json
import joblib
import warnings
from datetime import datetime
import re
import shutil
import sys

# ============================
# PATH CONFIGURATION
# ============================
script_dir = os.path.dirname(__file__)
compiled_input_path = os.path.normpath(os.path.join(script_dir, "..", "knowledge", "compiled_ml_data.json"))
materials_path = os.path.normpath(os.path.join(script_dir, "..", "knowledge", "materials.json"))
json_folder = os.path.normpath(os.path.join(script_dir, "..", "knowledge", "iterations"))
# model_path = r"C:\Users\CDH\Documents\Trabajo\IAAC\AIA\Studio\model\gwp_model_rf_av&gfa.pkl"  # old way
model_path =  os.path.normpath(os.path.join(script_dir, "..", "..", r"gwp_model_rf_av&gfa.pkl")) # automaticaly retrieve the ML model in the folder before the root folder
print("model to GWP PREDICTOR path:", model_path)

# ============================
# FUNCTION: Predict Outputs
# ============================

_loaded_model = None  # global model cache

def predict_outputs(inputs: dict, model_path: str) -> list:
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
        with open(materials_path, "r", encoding="utf-8") as mat_file:
            materials_map = json.load(mat_file)
    except Exception as e:
        print(f"Could not load materials.json: {e}")
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

        if full_key in materials_map:
            inputs_raw[full_key] = value
            decoded_value = materials_map[full_key].get(str(value), f"Unknown ({value})")
            inputs_decoded[full_key] = decoded_value
        else:
            inputs_raw[full_key] = value
            inputs_decoded[full_key] = value

    # Format outputs with readable labels
    formatted_outputs = {
        label.replace("\u00b2", "²"): round(value, 2)
        for label, value in zip(labels, outputs)
    } if outputs else "Prediction failed"

    version_data = {
        "version": version_name,
        "timestamp": datetime.now().isoformat(),
        "inputs_raw": inputs_raw,
        "inputs_decoded": inputs_decoded,
        "outputs": formatted_outputs
    }

    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(version_data, f, indent=4, ensure_ascii=False)
        print(f"Saved version file: {json_path}")
    except Exception as e:
        print(f"Failed to save JSON version: {e}")
    
    return version_name

# ============================
# MAIN EXECUTION
# ============================

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

default_inputs = {
    "ew_par": 1,
    "ew_ins": 2,
    "iw_par": 1,
    "es_ins": 1,
    "is_par": 0,
    "ro_par": 0,
    "ro_ins": 7,
    "wwr": 0.9,
    "av": 0.9,
    "gfa": 1000.0
}

# Load and merge input
try:
    with open(compiled_input_path, "r", encoding="utf-8") as f:
        loaded_inputs = json.load(f)
        inputs = {**default_inputs, **loaded_inputs}
except Exception as e:
    print(f"Failed to load compiled_ml_data.json, using default inputs: {e}")
    inputs = default_inputs

labels = [
    "Energy Intensity - EUI (kWh/m²a)",
    "Cooling Demand (kWh/m²a)",
    "Heating Demand (kWh/m²a)",
    "Operational Carbon (kg CO2e/m²a GFA)",
    "Embodied Carbon A1-A3 (kg CO2e/m²a GFA)",
    "Embodied Carbon A-D (kg CO2e/m²a GFA)",
    "GWP total (kg CO2e/m²a GFA)"
]


# Run prediction and save version
try:
    prediction = predict_outputs(inputs, model_path)
    print("\nPrediction Output:")
    for label, value in zip(labels, prediction):
        print(f"{label}: {value:.2f}")
except Exception as e:
    print(f"Prediction failed: {e}")
    prediction = []


# CONFIGURATION
source_folder = r'knowledge\iterations'
destination_folder = 'knowledge'
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


def cleanup_old_versions(folder: str, keep: int = 2):
    #"""Keep only the latest 2 versions of V*.json and V*.png files."""
    version_pattern = re.compile(r'^V(\d+)\.(json|png)$', re.IGNORECASE)

    try:
        files = os.listdir(folder)
        version_map = {}

        for file in files:
            match = version_pattern.match(file)
            if match:
                version = int(match.group(1))
                version_map.setdefault(version, []).append(file)

        sorted_versions = sorted(version_map.items(), key=lambda x: x[0], reverse=True)
        keep = sorted_versions[:2]
        delete = sorted_versions[2:]

        # Delete all older versions
        for version, file_list in delete:
            for file in file_list:
                path = os.path.join(folder, file)
                os.remove(path)
                print(f"🗑️ Deleted: {path}")

        # Rename the two most recent to V1 (latest), V0 (second latest)
        rename_map = {1: keep[0][0], 0: keep[1][0]} if len(keep) == 2 else {1: keep[0][0]}

        for target, original_version in rename_map.items():
            for ext in ["json", "png"]:
                old_filename = f"V{original_version}.{ext}"
                old_path = os.path.join(folder, old_filename)
                new_filename = f"V{target}.{ext}"
                new_path = os.path.join(folder, new_filename)

                if os.path.exists(old_path):
                    os.replace(old_path, new_path)
                    print(f"🔄 Renamed: {old_filename} → {new_filename}")

    except Exception as e:
        print(f"⚠️ Cleanup/Renaming error: {e}")


# Save versioned output
version_name = save_version_json(inputs, prediction, labels, json_folder)
copy_latest_version()
cleanup_old_versions(json_folder, keep=2)


# # Capture .png of iteration
# try:
#     sys.path.append(script_dir)
#     from SaveState_image import capture_viewport
#     capture_viewport(version_name, json_folder)
# except Exception as e:
#     print(f"Failed to capture viewport: {e}")
