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
    
    def map_materials_to_parameters(self, extracted_materials):
        """Convert extracted materials to parameter dictionary"""
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