import json

class MaterialMapper:
    def __init__(self):
        self.material_mappings = {
            "Ext.Wall_Partition": {
                "brick": 0, "concrete": 1, "earth": 2,
                "straw": 3, "timber_frame": 4, "timber_mass": 5
            },
            "Ext.Wall_Insulation": {
                "cellulose": 0, "cork": 1, "eps": 2,
                "glass_wool": 3, "mineral_wool": 4, "wood_fiber": 5
            },
            "Int.Wall_Partition": {
                "brick": 0, "concrete": 1, "earth": 2,
                "straw": 3, "timber_frame": 4, "timber_mass": 5
            },
            "Ext.Slab_Insulation": {
                "extruded_glas": 0, "xps": 1
            },
            "Int.Slab_Partition": {
                "concrete": 0, "timber_frame": 1, "timber_mass": 2
            },
            "Roof_Partition": {
                "concrete": 0, "timber_frame": 1, "timber_mass": 2
            },
            "Roof_Insulation": {
                "cellulose": 0, "cork": 1, "eps": 2, "extruded_glas": 3,
                "glass_wool": 4, "mineral_wool": 5, "wood_fiber": 6, "xps": 7
            }
        }
        
        # Reverse mapping for display
        self.value_to_material = {}
        for category, materials in self.material_mappings.items():
            self.value_to_material[category] = {v: k for k, v in materials.items()}
    
    def map_simple_material_to_parameters(self, simple_material):
        """Convert simple material category to detailed ML parameters"""
        
        # Default parameters structure
        parameters = {
            "ew_par": 0,   # External wall partition
            "ew_ins": 0,   # External wall insulation
            "iw_par": 0,   # Internal wall partition  
            "es_ins": 1,   # External slab insulation (default)
            "is_par": 0,   # Internal slab partition
            "ro_par": 0,   # Roof partition
            "ro_ins": 0    # Roof insulation
        }
        
        # Map simple material to detailed parameters
        material_lower = simple_material.lower()
        
        # External and internal wall partitions (same material)
        if material_lower in self.material_mappings["Ext.Wall_Partition"]:
            wall_value = self.material_mappings["Ext.Wall_Partition"][material_lower]
            parameters["ew_par"] = wall_value
            parameters["iw_par"] = wall_value
        
        # Roof and slab materials based on main material
        if material_lower in ["timber_frame", "timber_mass"]:
            # Timber buildings
            if material_lower == "timber_frame":
                parameters["is_par"] = 1  # Timber frame slab
                parameters["ro_par"] = 1  # Timber frame roof
            else:  # timber_mass
                parameters["is_par"] = 2  # Timber mass slab
                parameters["ro_par"] = 2  # Timber mass roof
        else:
            # Non-timber buildings default to concrete structure
            parameters["is_par"] = 0  # Concrete slab
            parameters["ro_par"] = 0  # Concrete roof
        
        # Default insulation (can be enhanced based on climate later)
        # For now, using defaults:
        # ew_ins = 0 (cellulose)
        # es_ins = 1 (xps) 
        # ro_ins = 0 (cellulose)
        
        print(f"[MATERIAL MAPPER] {simple_material} -> {parameters}")
        return parameters
    
    def map_materials_to_parameters(self, extracted_materials):
        """Convert extracted materials to parameter dictionary (existing method)"""
        parameters = {}
        
        # Mapping logic
        material_to_param = {
            "wall_material": ["ew_par", "iw_par"],
            "wall_insulation": ["ew_ins"],
            "roof_material": ["ro_par"],
            "roof_insulation": ["ro_ins"],
            "slab_material": ["is_par"],
            "slab_insulation": ["es_ins"]
        }
        
        for material_type, material_name in extracted_materials.items():
            param_keys = material_to_param.get(material_type, [])
            
            for param_key in param_keys:
                category = self.get_category_for_param(param_key)
                if category:
                    value = self.material_mappings[category].get(material_name.lower())
                    if value is not None:
                        parameters[param_key] = value
        
        return parameters
    
    def get_category_for_param(self, param_key):
        """Get material category for parameter key"""
        mapping = {
            "ew_par": "Ext.Wall_Partition",
            "iw_par": "Int.Wall_Partition", 
            "ew_ins": "Ext.Wall_Insulation",
            "ro_par": "Roof_Partition",
            "ro_ins": "Roof_Insulation",
            "is_par": "Int.Slab_Partition",
            "es_ins": "Ext.Slab_Insulation"
        }
        return mapping.get(param_key)
    
    def get_material_name(self, param_key, value):
        """Get material name from parameter value"""
        category = self.get_category_for_param(param_key)
        if category:
            return self.value_to_material[category].get(value, f"Unknown({value})")
        return f"Unknown({value})"