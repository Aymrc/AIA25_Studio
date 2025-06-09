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
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))

compiled_input_path = os.path.join(project_root, "knowledge", "compiled_ml_data.json")
materials_path = os.path.join(project_root, "knowledge", "materials.json")
json_folder = os.path.join(project_root, "knowledge", "iterations")
destination_folder = os.path.join(project_root, "knowledge")
destination_filename = "ml_output.json"

model_path = os.path.normpath(os.path.join(project_root, "..", "gwp_model_rf_av&gfa.pkl"))
print("model to GWP PREDICTOR path:", model_path)

# ============================
# INPUT NAME MAP
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

# ============================
# FUNCTION: Predict Outputs
# ============================
_loaded_model = None

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

    try:
        with open(materials_path, "r", encoding="utf-8") as mat_file:
            materials_map = json.load(mat_file)
    except Exception as e:
        print(f"Could not load materials.json: {e}")
        materials_map = {}

    existing_versions = [f for f in os.listdir(folder) if f.startswith("V") and f.endswith(".json")]
    existing_numbers = [int(f[1:-5]) for f in existing_versions if f[1:-5].isdigit()]
    next_version = max(existing_numbers, default=-1) + 1
    version_name = f"V{next_version}"
    json_path = os.path.join(folder, f"{version_name}.json")

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
# UTILITY: Create Manual Iteration (for Rhino listener)
# ============================

def create_manual_iteration(get_id_only=False, use_existing_id=None):
    dst_folder = json_folder
    os.makedirs(dst_folder, exist_ok=True)

    if use_existing_id:
        next_id = use_existing_id
    else:
        print(f"🧭 Writing to iteration folder: {dst_folder}")
        existing = [f for f in os.listdir(dst_folder) if f.startswith("I") and f.endswith(".json")]
        existing_numbers = [int(f[1:-5]) for f in existing if f[1:-5].isdigit()]
        next_number = max(existing_numbers, default=0) + 1
        next_id = f"I{next_number}"

    if get_id_only:
        return True, next_id

    dst_json = os.path.join(dst_folder, f"{next_id}.json")
    src_json = os.path.join(destination_folder, destination_filename)

    if not os.path.exists(src_json):
        return False, "❌ ml_output.json not found"

    try:
        shutil.copy2(src_json, dst_json)
        print(f"✅ Saved manual JSON: {dst_json}")
        return True, f"{next_id} created"
    except Exception as e:
        return False, f"❌ Error saving iteration: {e}"

# ============================
# EXPORTABLE SYMBOLS
# ============================
__all__ = ["create_manual_iteration"]

# ============================
# MAIN EXECUTION (only runs if called directly)
# ============================
if __name__ == "__main__":
    print("\n🧭 PATH VERIFICATION")
    print(f"📂 Script directory        : {script_dir}")
    print(f"📂 Project root            : {project_root}")
    print(f"📄 Compiled input path     : {compiled_input_path}")
    print(f"📄 Materials path          : {materials_path}")
    print(f"📁 Iterations (json_folder): {json_folder}")
    print(f"📁 Destination folder      : {destination_folder}")
    print(f"📄 Model path              : {model_path}")

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

    try:
        prediction = predict_outputs(inputs, model_path)
        print("\nPrediction Output:")
        for label, value in zip(labels, prediction):
            print(f"{label}: {value:.2f}")
    except Exception as e:
        print(f"Prediction failed: {e}")
        prediction = []

    version_name = save_version_json(inputs, prediction, labels, json_folder)
    latest_file_path = os.path.join(json_folder, version_name + ".json")
    if os.path.exists(latest_file_path):
        shutil.copy2(latest_file_path, os.path.join(destination_folder, destination_filename))
        print(f"Copied: {latest_file_path} → {destination_folder}/{destination_filename}")
