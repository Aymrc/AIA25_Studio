import json
import os

# !!!!!!!!!
# call this plot_loader at the end of the ML_predictor.py
# from UTILS.plot_data_loader import generate_plot_data
# generate_plot_data() 

json_folder = "Knowledge/Optioneering"
output_js = "UI/data/plot_data.js"

data_points = []

for filename in sorted(os.listdir(json_folder)):
    if filename.endswith(".json") and filename.startswith("V"):
        version = filename[:-5]
        with open(os.path.join(json_folder, filename), "r", encoding="utf-8") as f:
            data = json.load(f)
            try:
                gwp = data["outputs"]["GWP total (kg CO2e/m²a GFA)"]
                data_points.append({"version": version, "gwp": gwp})
            except Exception as e:
                print(f"Skipping {filename}: {e}")

with open(output_js, "w", encoding="utf-8") as out:
    out.write("window.gwpData = ")
    json.dump(data_points, out, indent=2)
    out.write(";")

print(f"GWP data exported to {output_js}")
