import os
import joblib
import warnings

# Output placeholder
prediction = "⚠️ Could not predict"
labeled_output = []

#Models
# Path to model file
model_path = r"C:\Users\User\Documents\IAAC\Module03\Encoding\ML\gwp_model_rf_av&gfa.pkl" #GFA+AV-based

# Default input values
defaults = {
    "ew_par": 0,
    "ew_ins": 0,
    "iw_par": 0,
    "es_ins": 0,
    "is_par": 0,
    "ro_par": 0,
    "ro_ins": 0,
    "wwr": 0.3,
    "av": 0.9,   
    "gfa":0.0
    #next versions will contain climate, energy, typology 
}

# Labels for prediction output
labels = [
    "Energy Intensity - EUI (kWh/sqm_GFA a)",
    "Cooling Demand (kWh/sqm_GFA a)",
    "Heating Demand (kWh/sqm_GFA a)",
    "Operational Carbon (kg CO2eq./sqm_GFA a)",
    "Embodied Carbon A1-A3 (kg CO2eq./sqm_GFA a)",
    "Embodied Carbon A-D (kg CO2eq./sqm_GFA a)",
    "GWP total (kg CO2eq./sqm_GFA a)"
]

# Assign values (use default or override below)
ew_par = defaults["ew_par"]
ew_ins = defaults["ew_ins"]
iw_par = defaults["iw_par"]
es_ins = defaults["es_ins"]
is_par = defaults["is_par"]
ro_par = defaults["ro_par"]
ro_ins = defaults["ro_ins"]
wwr = defaults["wwr"]
av = defaults["av"]
gfa = defaults["gfa"]


# Load model and make prediction
try:
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at: {model_path}")
    
    loaded_model = joblib.load(model_path)

    input_row = [[ew_par, ew_ins, iw_par, es_ins, is_par, ro_par, ro_ins, wwr, av, gfa]]

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        output = loaded_model.predict(input_row)[0]

    prediction = list(output)
    labeled_output = [f"{label}: {value:.2f}" for label, value in zip(labels, prediction)]

except Exception as e:
    prediction = f"⚠️ Prediction failed: {str(e)}"
    labeled_output = []

# Print each prediction line-by-line
print("Prediction Output:")
if labeled_output:
    for line in labeled_output:
        print(line)
else:
    print(prediction)

from datetime import datetime




# SaveState to Versions
import json
import os
from datetime import datetime

# Define folder for JSON version files
json_dir = r"Optioneering"
os.makedirs(json_dir, exist_ok=True)

# Get next version number
existing_versions = [f for f in os.listdir(json_dir) if f.startswith("V") and f.endswith(".json")]
existing_numbers = [int(f[1:-5]) for f in existing_versions if f[1:-5].isdigit()]
next_version = max(existing_numbers, default=-1) + 1
version_name = f"V{next_version}"
json_path = os.path.join(json_dir, f"{version_name}.json")

# Build version data
version_data = {
    "version": version_name,
    "timestamp": datetime.now().isoformat(),
    "inputs": {
        "ew_par": ew_par,
        "ew_ins": ew_ins,
        "iw_par": iw_par,
        "es_ins": es_ins,
        "is_par": is_par,
        "ro_par": ro_par,
        "ro_ins": ro_ins,
        "wwr": wwr,
        "av": av,
        "gfa": gfa
    },
    "outputs": dict(zip(labels, prediction)) if labeled_output else "Prediction failed"
}

# Save JSON file
try:
    with open(json_path, "w") as f:
        json.dump(version_data, f, indent=4)
    print(f"✅ Saved: {json_path}")
except Exception as e:
    print(f"⚠️ Failed to save version JSON: {e}")

