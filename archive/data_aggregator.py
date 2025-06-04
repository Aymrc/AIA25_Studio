import json
import os
from utils.ml_utils import load_ml_predictions


def load_json(path):
    if not os.path.exists(path):
        print(f"⚠️ File not found: {path}")
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load {path}: {e}")
        return {}


def get_combined_design_data():
    base_path = os.path.join(os.path.dirname(__file__), '..', 'knowledge')

    design_data = load_json(os.path.join(base_path, 'design.json'))
    config_data = load_json(os.path.join(base_path, 'config.json'))
    ml_data = load_ml_predictions(os.path.join(base_path, 'ml_output.json'))

    # Merge all data into one dictionary (ML data overwrites others if keys overlap)
    combined = {**design_data, **config_data, **ml_data}
    return combined
