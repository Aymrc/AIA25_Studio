import time
import os
import re

from utils.file_watcher import FileWatcher
from utils.data_aggregator import get_combined_design_data


def start_file_watcher():
    base_path = os.path.dirname(__file__)
    watch_dir = os.path.join(base_path, "knowledge")

    if not os.path.exists(watch_dir):
        raise FileNotFoundError(f"📁 Folder '{watch_dir}' not found. Please create it inside your project directory.")

    watcher = FileWatcher(
        watch_directory=watch_dir,
        target_files=['design.json', 'params.txt', 'config.json', 'ml_output.json'],
        design_data_callback=get_combined_design_data
    )

    watcher.start_watching()
    return watcher


def main():
    watcher = start_file_watcher()

    try:
        print("📡 Passive agent is running. Waiting for ml_output.json updates...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        if watcher:
            watcher.stop_watching()


if __name__ == "__main__":
    main()
