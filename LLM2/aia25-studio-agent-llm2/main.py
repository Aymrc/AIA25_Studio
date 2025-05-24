import threading
import time
from server.config import *
from llm_calls import *
from utils.file_watcher import FileWatcher
import json
import os
import re

# Placeholder design data (replace later with actual GH or JSON input)
design_data = {
    "materials": ["concrete", "glass", "timber"],
    "embodied_carbon": "420 kgCO₂e/m²",
    "solar_radiation_area": "380 m²",
    "number_of_levels": 6,
    "typology": "block",  # Options: courtyard, block, L-shaped
    "unit_counts": {
        "3BD": 8,
        "2BD": 12,
        "1BD": 10
    },
    "GFA": "2,400 m²",
    "plot_dimensions": "30m x 40m"
}

def get_current_design_data():
    """Returns current design data"""
    return design_data


def start_file_watcher():
    base_path = os.path.dirname(__file__)  # carpeta del script
    watch_dir = os.path.join(base_path, "knowledge")

    if not os.path.exists(watch_dir):
        raise FileNotFoundError(f"📁 Folder '{watch_dir}' not found. Please create it inside your project directory.")

    watcher = FileWatcher(
        watch_directory=watch_dir,
        target_files=['design.json', 'params.txt', 'config.json'],
        design_data_callback=get_current_design_data
    )
    
    watcher.start_watching()
    return watcher


def clean_llm_output(text):
    """Remove any <think>...</think> blocks from model responses."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def main():
    print("\n👋 " + clean_llm_output(query_intro()))

    # Start file watcher in separate thread
    watcher = start_file_watcher()

    try:
        while True:
            user_input = input("\n💬 What would you like to know about your design? (type 'exit' to quit)\n> ")

            if user_input.lower() in ["exit", "quit"]:
                print("👋 Goodbye!")
                break

            lowered = user_input.lower()
            change_keywords = ["change", "replace", "switch", "update", "make it", "modify", "set", "turn into"]
            improve_keywords = ["improve", "reduce", "maximize", "minimize", "optimize", "should i", "could i", "recommend", "how can i"]

            if any(kw in lowered for kw in change_keywords):
                result = suggest_change(user_input, design_data)
                print("\n🛠 Change Instruction:")
                print(clean_llm_output(result))

            elif any(kw in lowered for kw in improve_keywords):
                suggestion = suggest_improvements(user_input, design_data)
                print("\n🧩 Suggestion:")
                print(clean_llm_output(suggestion))

            else:
                reply = answer_user_query(user_input, design_data)
                print("\n📊 Data Insight:")
                print(clean_llm_output(reply))

    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        if watcher:
            watcher.stop_watching()


if __name__ == "__main__":
    main()
