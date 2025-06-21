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
# DEBUG PATH VERIFICATION
# ============================
print("\n🧭 PATH VERIFICATION")
print(f"📂 Script directory        : {script_dir}")
print(f"📂 Project root            : {project_root}")
print(f"📄 Compiled input path     : {compiled_input_path}")
print(f"📄 Materials path          : {materials_path}")
print(f"📁 Iterations (json_folder): {json_folder}")
print(f"📁 Destination folder      : {destination_folder}")
print(f"📄 Model path              : {model_path}")


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

    existing_versions = [f for f in os.listdir(folder) if f.startswith("I") and f.endswith(".json")]
    existing_numbers = [int(f[1:-5]) for f in existing_versions if f[1:-5].isdigit()]
    next_version = max(existing_numbers, default=-1) + 1
    version_name = f"I{next_version}"
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
# MAIN EXECUTION
# ============================

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

# ============================
# VERSION MANAGEMENT
# ============================

version_pattern = re.compile(r'I(\d+)', re.IGNORECASE)

def get_version(filename):
    match = version_pattern.search(filename)
    return int(match.group(1)) if match else -1

def find_latest_version_file(folder):
    files = os.listdir(folder)
    versioned_files = [(f, get_version(f)) for f in files if get_version(f) != -1]
    if not versioned_files:
        return None
    latest_file = max(versioned_files, key=lambda x: x[1])[0]
    return os.path.join(folder, latest_file)

def copy_latest_version():
    latest_file_path = find_latest_version_file(json_folder)
    if latest_file_path:
        dest_path = os.path.join(destination_folder, destination_filename)
        shutil.copy2(latest_file_path, dest_path)
        print(f"Copied: {latest_file_path} -> {dest_path}")
    else:
        print("No versioned files found.")

#WIP (Andres)
# def create_manual_iteration(get_id_only=False, use_existing_id=None):
#     dst_folder = json_folder
#     os.makedirs(dst_folder, exist_ok=True)

#     if use_existing_id:
#         next_id = use_existing_id
#     else:
#         print(f"🧭 Writing to iteration folder: {dst_folder}")
#         existing = [f for f in os.listdir(dst_folder) if f.startswith("I") and f.endswith(".json")]
#         existing_numbers = [int(f[1:-5]) for f in existing if f[1:-5].isdigit()]
#         next_number = max(existing_numbers, default=0) + 1
#         next_id = f"I{next_number}"

#     if get_id_only:
#         return True, next_id

#     dst_json = os.path.join(dst_folder, f"{next_id}.json")
#     src_json = os.path.join(destination_folder, destination_filename)

#     if not os.path.exists(src_json):
#         return False, "❌ ml_output.json not found"

#     try:
#         shutil.copy2(src_json, dst_json)
#         print(f"✅ Saved manual JSON: {dst_json}")
#         # No need to move images — they are saved directly by Rhino
#         return True, f"{next_id} created"
#     except Exception as e:
#         return False, f"❌ Error saving iteration: {e}"


#WIP (Andres)
def cleanup_old_versions(folder: str, keep: int = 2):
    """
    Keeps only the latest two manual iteration files (e.g., I1.json, I2.png),
    and renames the latest as In.* and second-latest as In-1.*
    Deletes older ones.
    """
    version_pattern = re.compile(r'^I(\d+)\.(json|png)$', re.IGNORECASE)
    files = os.listdir(folder)
    versioned_files = {}

    # Group files by iteration number
    for file in files:
        match = version_pattern.match(file)
        if match:
            version = int(match.group(1))
            versioned_files.setdefault(version, []).append(file)

    if len(versioned_files) < 2:
        print("⚠️ Less than two iterations found — skipping cleanup.")
        return

    # Sort and select the two most recent iterations
    sorted_versions = sorted(versioned_files.keys(), reverse=True)
    latest = sorted_versions[0]
    second_latest = sorted_versions[1]

    # Define alias mapping
    mapping = {
        latest: "In",
        second_latest: "In-1"
    }

    # Copy latest iterations with aliases
    for original_version, alias in mapping.items():
        for ext in ["json", "png"]:
            for view_type in ["", "_user", "_axon"]:
                original = f"I{original_version}{view_type}.{ext}"
                if original in files:
                    src = os.path.join(folder, original)
                    dst = os.path.join(folder, f"{alias}{view_type}.{ext}")
                    try:
                        shutil.copy2(src, dst)
                        print(f"✅ Copied {original} → {alias}{view_type}.{ext}")
                    except Exception as e:
                        print(f"⚠️ Failed to copy {original}: {e}")

    # Delete all other iterations
    for version, version_files in versioned_files.items():
        if version not in mapping:
            for filename in version_files:
                try:
                    os.remove(os.path.join(folder, filename))
                    print(f"🗑️ Deleted: {filename}")
                except Exception as e:
                    print(f"⚠️ Failed to delete {filename}: {e}")


def copy_last_two_versions_as_iterations(folder: str):
    #Copies the last two versioned JSON files (V*.json) to In.json and In-1.json.
    #No files are deleted or renamed.
    
    version_pattern = re.compile(r"^I(\d+)\.json$", re.IGNORECASE)
    files = os.listdir(folder)
    print("📄 All files in folder:")
    
    # Extract version numbers from V*.json
    versioned = [(f, int(match.group(1)))
                 for f in files
                 if (match := version_pattern.match(f))]

    if len(versioned) < 2:
        print("⚠️ Not enough I*.json files found to copy.")
        return

    # Sort by version number descending
    versioned.sort(key=lambda x: x[1], reverse=True)
    latest, second_latest = versioned[0][0], versioned[1][0]

    # Prepare source and destination paths
    latest_src = os.path.join(folder, latest)
    latest_dst = os.path.join(folder, "In.json")

    second_src = os.path.join(folder, second_latest)
    second_dst = os.path.join(folder, "In-1.json")

    try:
        shutil.copy2(latest_src, latest_dst)
        print(f"✅ Copied {latest} → In.json")

        shutil.copy2(second_src, second_dst)
        print(f"✅ Copied {second_latest} → In-1.json")

    except Exception as e:
        print(f"❌ Error during copy: {e}")





# === MAIN FLOW ===
version_name = save_version_json(inputs, prediction, labels, json_folder)
copy_latest_version()
copy_last_two_versions_as_iterations(json_folder)
cleanup_old_versions(json_folder, keep=2)
