import json
import os
import re
import traceback
from server.config import client, completion_model

# =====================================
# Version Utilities for Historical Analysis
# =====================================

def list_all_version_files(folder="knowledge/iterations"):
    """Return a sorted list of all version filenames like V1.json, V2.json..."""
    try:
        files = [f for f in os.listdir(folder) if re.match(r"^V\d+\.json$", f)]
        return sorted(files, key=lambda x: int(re.search(r"\d+", x).group()))
    except Exception as e:
        print(f"[VERSION LIST] Error: {e}")
        return []

def load_specific_version(version_name, folder="knowledge/iterations"):
    """Load and return the JSON for a specific version like 'V3'"""
    try:
        path = os.path.join(folder, f"{version_name}.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[LOAD VERSION] Error loading {version_name}: {e}")
        return None

def summarize_version_outputs(folder="knowledge/iterations"):
    """Return a list of version summaries (version + outputs only)"""
    summaries = []
    for filename in list_all_version_files(folder):
        try:
            with open(os.path.join(folder, filename), "r", encoding="utf-8") as f:
                data = json.load(f)
                summaries.append({
                    "version": filename.replace(".json", ""),
                    "outputs": data.get("outputs", {})
                })
        except Exception as e:
            print(f"[SUMMARY ERROR] {filename}: {e}")
    return summaries

def get_best_version(metric="GWP total", folder="knowledge/iterations"):
    """Find the version with the lowest specified output metric"""
    summaries = [s for s in summarize_version_outputs(folder) if s["version"].startswith("V")]
    best = None
    best_val = float("inf")
    for entry in summaries:
        val = entry["outputs"].get(metric)
        if isinstance(val, (int, float)) and val < best_val:
            best = entry["version"]
            best_val = val
    return best, best_val

def load_version_details(version_name, folder="knowledge/iterations"):
    """
    Load a specific version file based on exact version name (e.g., 'V7').
    """
    filename = f"{version_name}.json"
    path = os.path.join(folder, filename)

    if not os.path.exists(path):
        print(f"[LOAD VERSION] File not found: {path}")
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[LOAD VERSION] Failed to load {path}: {e}")
        return None


def extract_versions_from_input(user_input):
    """Return all version mentions like V1, V7, V12 (case-insensitive)."""
    return re.findall(r'\bV\d+\b', user_input.upper())

def summarize_versions_data(version_names, folder="knowledge/iterations"):
    """Return dict of version_name -> {inputs_decoded, outputs} for selected versions"""
    result = {}
    for v in version_names:
        data = load_version_details(v, folder)
        if data:
            result[v] = {
                "inputs_decoded": data.get("inputs_decoded", {}),
                "outputs": data.get("outputs", {})
            }
    return result
