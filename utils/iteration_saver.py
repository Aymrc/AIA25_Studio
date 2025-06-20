# -*- coding: utf-8 -*-
import os
import shutil

# This function is designed for use with IronPython in Rhino
def create_manual_iteration(destination_folder, destination_filename, json_folder):
    # Ensure the destination folder exists (IronPython-safe: check before creating)
    if not os.path.exists(json_folder):
        os.makedirs(json_folder)

    # Find existing iteration files like I1.json, I2.json, etc.
    existing = [f for f in os.listdir(json_folder) if f.startswith("I") and f.endswith(".json")]
    existing_numbers = [int(f[1:-5]) for f in existing if f[1:-5].isdigit()]
    next_number = max(existing_numbers) + 1 if existing_numbers else 1
    next_id = "I{}".format(next_number)

    # Set full paths
    dst_json = os.path.join(json_folder, "{}.json".format(next_id))
    src_json = os.path.join(destination_folder, destination_filename)

    # Check that source exists
    if not os.path.exists(src_json):
        return False, "Error: ml_output.json not found"

    try:
        shutil.copy2(src_json, dst_json)
        return True, next_id
    except Exception as e:
        return False, "Error saving iteration: {}".format(e)
