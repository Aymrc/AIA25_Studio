import threading
import time
import os
import re

from server.config import *
from llm_calls import *
from utils.file_watcher import FileWatcher
from utils.data_aggregator import get_combined_design_data
from utils.intent_router import classify_intent
from utils.retrieveKPIdata import get_kpis
from utils.load_options import generate_paths


def start_file_watcher():
    base_path = os.path.dirname(__file__)
    watch_dir = os.path.join(base_path, "knowledge")

    if not os.path.exists(watch_dir):
        raise FileNotFoundError(f"📁 Folder '{watch_dir}' not found. Please create it inside your project directory.")

    watcher = FileWatcher(
        watch_directory=watch_dir,
        target_files=['design.json', 'params.txt', 'config.json'],
        design_data_callback=get_combined_design_data
    )

    watcher.start_watching()
    return watcher


def clean_llm_output(text):
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def main():
    print("\n👋 " + clean_llm_output(query_intro()))

    watcher = start_file_watcher()

    try:
        while True:
            user_input = input("\n💬 What would you like to know about your design? (type 'exit' to quit)\n> ")

            if user_input.lower() in ["exit", "quit"]:
                print("👋 Goodbye!")
                break

            design_data = get_combined_design_data()
            intent = classify_intent(user_input)

            if intent == "design_change":
                result = suggest_change(user_input, design_data)
                print("\n💖 Change Instruction:")
                print(clean_llm_output(result))

            elif intent == "suggestion":
                suggestion = suggest_improvements(user_input, design_data)
                print("\n🧩 Suggestion:")
                print(clean_llm_output(suggestion))

            elif intent == "data_query":
                kpis = get_kpis(design_data, user_input)
                print("\n📊 KPI Insight:")
                print(clean_llm_output(kpis))

            elif intent == "fallback":
                options = generate_paths(design_data)
                print("\n🚀 Optioneering Suggestions:")
                print(clean_llm_output(options))

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
