# file_watcher.py
import json
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from llm_calls import *

import re

def clean_llm_output(text):
    """Remove <think>...</think> blocks from LLM output"""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


class DesignFileHandler(FileSystemEventHandler):
    def __init__(self, target_files, design_data_callback=None):
        """
        target_files: list of files to monitor (e.g: ['design.json', 'params.txt'])
        design_data_callback: function that returns current design data
        """
        self.target_files = [Path(f).name for f in target_files]
        self.design_data_callback = design_data_callback
        self.last_modified = {}


    def on_modified(self, event):
        if event.is_directory:
            return
            
        file_name = Path(event.src_path).name
        
        # Only process target files
        if file_name not in self.target_files:
            return
            
        # Avoid multiple triggers for same event
        current_time = time.time()
        if file_name in self.last_modified:
            if current_time - self.last_modified[file_name] < 1:  # 1 second debounce
                return
        
        self.last_modified[file_name] = current_time
        
        print(f"\n🔄 {file_name} has been modified!")
        self.handle_file_change(event.src_path, file_name)
    

    def handle_file_change(self, file_path, file_name):
        """Handles file change and queries the LLM"""
        try:
            # Read content of modified file
            file_content = self.read_file_content(file_path)

            # Get current design data
            current_design = self.design_data_callback() if self.design_data_callback else {}

            # Generate automatic query
            auto_query = self.generate_auto_query(file_name, file_content, current_design)

            # print(f"\n🤖 Auto-generated insight:")
            print(clean_llm_output(auto_query))  # <--- clean output here

            # Optional: ask user if they want to do something
            user_response = input(f"\n💭 Would you like me to suggest improvements based on this change? (y/n): ")
            if user_response.lower() in ['y', 'yes']:
                suggestion = suggest_improvements(
                    f"The {file_name} file was updated. What improvements can you suggest?",
                    current_design
                )
                print(f"\n💡 Suggestion:")
                print(clean_llm_output(suggestion))  # <--- clean suggestion too

        except Exception as e:
            print(f"❌ Error processing file change: {e}")
   

    def read_file_content(self, file_path):
        """Reads content of modified file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # If JSON, try to parse it
            if file_path.endswith('.json'):
                return json.loads(content)
            return content
            
        except Exception as e:
            print(f"⚠️ Warning: Could not read {file_path}: {e}")
            return None
    

    def generate_auto_query(self, file_name, file_content, design_data):
        """Generates automatic query based on file change"""
        
        # Create context for LLM
        context_prompt = f"""
        A design file '{file_name}' was just modified. 
        
        Based on this change and the current design data, provide a brief insight or observation about what might have changed and its potential impact.
        
        Keep it concise (1-2 sentences) and focused on design implications.
        """
        
        design_data_json = json.dumps(design_data)
        file_content_str = json.dumps(file_content) if isinstance(file_content, dict) else str(file_content)[:500]  # Limit content
        
        response = client.chat.completions.create(
            model=completion_model,
            messages=[
                {
                    "role": "system",
                    "content": f"""
                    You are a design assistant. A file was just modified in a design project.
                    
                    Current design data: {design_data_json}
                    Modified file content (first 500 chars): {file_content_str}
                    
                    {context_prompt}
                    """
                }
            ]
        )
        
        return response.choices[0].message.content


class FileWatcher:
    def __init__(self, watch_directory=".", target_files=None, design_data_callback=None):
        """
        watch_directory: directory to monitor
        target_files: list of specific files to monitor
        design_data_callback: function that returns current design data
        """
        self.watch_directory = watch_directory
        self.target_files = target_files or ['design.json', 'params.txt', 'config.json']
        self.design_data_callback = design_data_callback
        self.observer = None


    def start_watching(self):
        """Starts file monitoring"""
        event_handler = DesignFileHandler(self.target_files, self.design_data_callback)
        self.observer = Observer()
        self.observer.schedule(event_handler, self.watch_directory, recursive=False)
        self.observer.start()
        
        print(f"📁 File watcher started. Monitoring: {', '.join(self.target_files)}")
        print(f"📂 Watching directory: {Path(self.watch_directory).absolute()}")


    def stop_watching(self):
        """Stops monitoring"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            print("🛑 File watcher stopped.")
    

    def is_running(self):
        """Checks if watcher is running"""
        return self.observer and self.observer.is_alive()


# Helper function
def get_current_design_data():
    """Helper function that returns current design data"""
    # Here you can load from file or return your hardcoded data
    return {
        "materials": ["concrete", "glass", "timber"],
        "embodied_carbon": "420 kgCO₂e/m²",
        "solar_radiation_area": "380 m²",
        "number_of_levels": 6,
        "typology": "block",
        "unit_counts": {"3BD": 8, "2BD": 12, "1BD": 10},
        "GFA": "2,400 m²",
        "plot_dimensions": "30m x 40m"
    }


if __name__ == "__main__":
    # Test file watcher
    watcher = FileWatcher(
        watch_directory=".",
        target_files=['design.json', 'params.txt', 'test.json'],
        design_data_callback=get_current_design_data
    )
    
    try:
        watcher.start_watching()
        print("Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watcher.stop_watching()
        print("Bye!")