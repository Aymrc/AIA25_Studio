import json
import os
import time

class KnowledgeCompiler:
    def __init__(self):
        self.knowledge_folder = "knowledge"
        
    def compile_all_data(self):
        """Compile all knowledge into ML-ready dictionary"""
        try:
            compiled_data = {}
            
            # Load design parameters (materials, WWR)
            params_file = os.path.join(self.knowledge_folder, "design_parameters.json")
            if os.path.exists(params_file):
                with open(params_file, 'r') as f:
                    params = json.load(f)
                compiled_data.update(params)
            
            # Load Rhino geometry data (GFA, compactness)
            rhino_file = os.path.join(self.knowledge_folder, "rhino_geometry.json")
            if os.path.exists(rhino_file):
                with open(rhino_file, 'r') as f:
                    rhino_data = json.load(f)
                if "gfa" in rhino_data:
                    compiled_data["gfa"] = rhino_data["gfa"]
                if "av" in rhino_data:
                    compiled_data["av"] = rhino_data["av"]
            
            # Add defaults for missing values
            defaults = {
                "ew_par": 1,    # Default concrete
                "ew_ins": 2,    # Default EPS
                "iw_par": 1,    # Default concrete
                "es_ins": 1,    # Default XPS
                "is_par": 0,    # Default concrete
                "ro_par": 0,    # Default concrete
                "ro_ins": 7,    # Default XPS
                "wwr": 0.3,     # Default 30%
                "gfa": 200.0,   # Default GFA
                "av": 0.5       # Default compactness
            }
            
            for key, default_value in defaults.items():
                if key not in compiled_data:
                    compiled_data[key] = default_value
            
            # Add metadata
            compiled_data["compiled_timestamp"] = time.time()
            compiled_data["data_sources"] = self.get_data_sources()
            
            # Save compiled data
            compiled_file = os.path.join(self.knowledge_folder, "compiled_ml_data.json")
            with open(compiled_file, 'w') as f:
                json.dump(compiled_data, f, indent=2)
            
            return compiled_data
            
        except Exception as e:
            print(f"Compilation error: {e}")
            return {}
    
    def get_data_sources(self):
        """Get info about data sources"""
        sources = {}
        
        params_file = os.path.join(self.knowledge_folder, "design_parameters.json")
        if os.path.exists(params_file):
            sources["materials_wwr"] = "user_input"
        
        rhino_file = os.path.join(self.knowledge_folder, "rhino_geometry.json")
        if os.path.exists(rhino_file):
            sources["geometry"] = "rhino_monitor"
        
        return sources
    
    def get_compiled_data(self):
        """Get current compiled data"""
        compiled_file = os.path.join(self.knowledge_folder, "compiled_ml_data.json")
        
        if os.path.exists(compiled_file):
            with open(compiled_file, 'r') as f:
                return json.load(f)
            
            # path_ML = "utils\ML_predictor.py"
            # subprocess.Popen([python_path, path_ML], creationflags=0, cwd=script_dir)
        else:
            return self.compile_all_data()
         