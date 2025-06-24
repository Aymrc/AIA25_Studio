import os
import json
import joblib
import warnings
from datetime import datetime
import re
import shutil
import sys

import torch
import clip
from PIL import Image


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

model_path = "lightgbm_multi.pkl"
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
        "Typology": "Typology",
        "WWR": "Window-to-Wall_Ratio",
        "EW_PAR": "Ext.Wall_Partition",
        "EW_INS": "Ext.Wall_Insulation",
        "IW_PAR": "Int.Wall_Partition",
        "ES_INS": "Ext.Slab_Insulation",
        "IS_PAR": "Int.Slab_Partition",
        "RO_PAR": "Roof_Partition",
        "RO_INS": "Roof_Insulation",
        "BC": "Beams & Columns",
        "Volume(m3)": "Volume",
        "A/V": "Compactness",
        "VOL/VOLBBOX": "Shape-Efficiency"
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

    input_order = [
    "Typology", "WWR", "EW_PAR", "EW_INS", "IW_PAR",
    "ES_INS", "IS_PAR", "RO_PAR", "RO_INS", "BC",
    "Volume(m3)", "A/V", "VOL/VOLBBOX" ]
    
    input_row = [[inputs[k] for k in input_order]]

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        output = _loaded_model.predict(input_row)[0]

    return list(output)

# ============================
# FUNCTION: Save Version JSON
# ============================

def clip_Gaia(latest_image_path):
    # Set device
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Load CLIP model and preprocessing
    model, preprocess = clip.load("ViT-B/32", device=device)
    model.eval()

    # Load trained classifier and class names
    script_dir = os.path.dirname(os.path.abspath(__file__))
    clip_model_path = os.path.join(script_dir, "clip_finetuned_w_linear_classifier.pkl")

    if not os.path.exists(clip_model_path):
        raise FileNotFoundError(f"Classifier .pkl not found at: {clip_model_path}")

    checkpoint = joblib.load(clip_model_path)
    clf = checkpoint["classifier"]
    class_names = checkpoint["class_names"]

    # Load and preprocess image
    image = preprocess(Image.open(latest_image_path).convert("RGB")).unsqueeze(0).to(device)

    # Encode image using CLIP
    with torch.no_grad():
        image_feature = model.encode_image(image)
        image_feature /= image_feature.norm(dim=-1, keepdim=True)
        image_feature = image_feature.cpu().numpy()

    # Predict using classifier
    pred_class = clf.predict(image_feature)[0]
    pred_label = class_names[pred_class]

    print(f"Predicted typology: {pred_label}")
    return pred_label

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



    existing_versions_clip = [f for f in os.listdir(folder) if f.startswith("V") and f.endswith(".json")]
    existing_numbers_clip = [int(f[1:-5]) for f in existing_versions_clip if f[1:-5].isdigit()]
    next_version_clip = max(existing_numbers_clip, default=-1)
    version_name_clip = f"V{next_version_clip}"

    latest_image_filename = version_name_clip + ".png"
    latest_image_path = os.path.join(folder, latest_image_filename)
    typology_prediction = clip_Gaia(latest_image_path) # calling CLIP on the latest png
    print(typology_prediction)
    # inputs["Typology"] = typology_prediction


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
    "Typology": 1,
    "WWR": 3,
    "EW_PAR": 2,
    "EW_INS": 3,
    "IW_PAR": 1,
    "ES_INS": 1,
    "IS_PAR": 2,
    "RO_PAR": 1,
    "RO_INS": 2,
    "BC": 2,
    "Volume(m3)": 5000,
    "A/V": 0.4,
    "VOL/VOLBBOX": 0.6
}

try:
    with open(compiled_input_path, "r", encoding="utf-8") as f:
        loaded_inputs_raw = json.load(f)

        rename_map = {
            "av": "A/V", "gfa": "Volume(m3)", "volbbox": "VOL/VOLBBOX",
            "wwr": "WWR", "ew_par": "EW_PAR", "ew_ins": "EW_INS",
            "iw_par": "IW_PAR", "es_ins": "ES_INS", "is_par": "IS_PAR",
            "ro_par": "RO_PAR", "ro_ins": "RO_INS", "bc": "BC", "typology": "Typology"
        }

        corrected_inputs = {
            rename_map.get(k, k): v for k, v in loaded_inputs_raw.items()
        }

        required_keys = list(default_inputs.keys())
        inputs = {k: corrected_inputs.get(k, default_inputs[k]) for k in required_keys}

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
