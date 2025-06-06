import json
import os

# !!!!!!!!!
# call this plot_loader at the end of the ML_predictor.py
# from UTILS.plot_data_loader import generate_plot_data
# generate_plot_data() 

json_folder = "knowledge\iterations"
output_js = "ui/data/plot_data.js"

metrics = {
    "GWP total (kg CO2e/m²a GFA)": "GWP total",
    "Operational Carbon (kg CO2e/m²a GFA)": "Op. Carbon",
    "Embodied Carbon A-D (kg CO2e/m²a GFA)": "EC A-D",
    "Energy Intensity - EUI (kWh/m²a)": "EUI",
    "Cooling Demand (kWh/m²a)": "Cooling",
    "Heating Demand (kWh/m²a)": "Heating"
}

data_points = []


for filename in sorted(os.listdir(json_folder)):
    if filename.endswith(".json") and filename.startswith("V"):
        version = filename[:-5]
        filepath = os.path.join(json_folder, filename)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            outputs = data.get("outputs", {})
            entry = {"version": version}

            for metric in metrics:
                # Fuzzy match the metric key
                for key, val in outputs.items():
                    if key.startswith(metric):
                        entry[key] = round(val, 2)
                        break

            data_points.append(entry)

        except Exception as e:
            print(f"Skipping {filename}: {e}")



with open(output_js, "w", encoding="utf-8") as out:
    out.write("window.gwpData = ")
    json.dump(data_points, out, indent=2)
    out.write(";")

print(f"GWP data exported to {output_js}")
