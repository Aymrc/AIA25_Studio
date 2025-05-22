import json
import time
import re
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from llm_calls import *

# Constants
DEBOUNCE_SECONDS = 1

def clean_llm_output(text: str) -> str:
    """Remove <think>...</think> blocks from LLM output."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

class DesignFileHandler(FileSystemEventHandler):
    def __init__(self, target_files, design_data_callback=None):
        self.target_files = [Path(f).name for f in target_files]
        self.design_data_callback = design_data_callback
        self.last_modified = {}


    def on_modified(self, event):
        if event.is_directory:
            return

        file_name = Path(event.src_path).name
        if file_name not in self.target_files:
            return

        current_time = time.time()
        if file_name in self.last_modified:
            if current_time - self.last_modified[file_name] < DEBOUNCE_SECONDS:
                return

        self.last_modified[file_name] = current_time
        print(f"\n🔄 {file_name} has been modified!")
        self.handle_file_change(event.src_path, file_name)


    def handle_file_change(self, file_path, file_name):
        try:
            file_content = self.read_file_content(file_path)
            current_design = self.design_data_callback() if self.design_data_callback else {}
            auto_query = self.generate_auto_query(file_name, file_content, current_design)

            print("\n🤖 Auto-generated insight:")
            print(clean_llm_output(auto_query))

            user_response = input("\n💭 Would you like me to suggest improvements based on this change? (y/n): ")
            if user_response.strip().lower() in {'y', 'yes'}:
                suggestion = suggest_improvements(
                    f"The {file_name} file was updated. What improvements can you suggest?",
                    current_design
                )
                print("\n💡 Suggestion:")
                print(clean_llm_output(suggestion))

        except Exception as e:
            print(f"❌ Error processing file change: {e}")


    def read_file_content(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return json.loads(content) if file_path.endswith('.json') else content
        except Exception as e:
            print(f"⚠️ Warning: Could not read {file_path}: {e}")
            return None


    def generate_auto_query(self, file_name, file_content, design_data):
        design_data_json = json.dumps(design_data)
        file_content_str = json.dumps(file_content) if isinstance(file_content, dict) else str(file_content)[:500]

        prompt = f"""
        A design file '{file_name}' was just modified.
        Based on this change and the current design data, provide a brief insight or observation about what might have changed and its potential impact.
        Keep it concise (1-2 sentences) and focused on design implications.
        """

        response = client.chat.completions.create(
            model=completion_model,
            messages=[
                {
                    "role": "system",
                    "content": f"""
                    You are a design assistant. A file was just modified in a design project.

                    Current design data: {design_data_json}
                    Modified file content (first 500 chars): {file_content_str}

                    {prompt}
                    """
                }
            ]
        )

        return response.choices[0].message.content


class FileWatcher:
    def __init__(self, watch_directory=".", target_files=None, design_data_callback=None):
        self.watch_directory = watch_directory
        self.target_files = target_files or ['design.json', 'params.txt', 'config.json']
        self.design_data_callback = design_data_callback
        self.observer = None


    def start_watching(self):
        handler = DesignFileHandler(self.target_files, self.design_data_callback)
        self.observer = Observer()
        self.observer.schedule(handler, self.watch_directory, recursive=False)
        self.observer.start()

        print(f"📁 File watcher started. Monitoring: {', '.join(self.target_files)}")
        print(f"📂 Watching directory: {Path(self.watch_directory).absolute()}")


    def stop_watching(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            print("🛑 File watcher stopped.")


    def is_running(self):
        return self.observer and self.observer.is_alive()
