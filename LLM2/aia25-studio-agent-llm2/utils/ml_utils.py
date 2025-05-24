import json
import os

def flatten_ml_data(nested):
    flat = {}
    for category, metrics in nested.items():
        for label, value in metrics.items():
            key = f"{category}_{label}"
            flat[key] = value
    return flat


def load_ml_predictions(path="knowledge/ml_output.json"):
    if not os.path.exists(path):
        print(f"⚠️ No ML prediction file found at: {path}")
        return {}

    try:
        with open(path, "r", encoding='utf-8') as file:
            nested = json.load(file)
            return flatten_ml_data(nested)
    except Exception as e:
        print(f"❌ Failed to load ML prediction file: {e}")
        return {}

