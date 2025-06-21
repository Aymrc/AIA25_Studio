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

        self.value_to_material = {
            category: {v: k for k, v in mapping.items()}
            for category, mapping in self.material_mappings.items()
        }

    def map_simple_material_to_parameters(self, simple_material):
        parameters = {
            "EW_PAR": 0,
            "EW_INS": 0,
            "IW_PAR": 0,
            "ES_INS": 1,
            "IS_PAR": 0,
            "RO_PAR": 0,
            "RO_INS": 0
        }

        material = simple_material.lower()

        if material in self.material_mappings["Ext.Wall_Partition"]:
            val = self.material_mappings["Ext.Wall_Partition"][material]
            parameters["EW_PAR"] = val
            parameters["IW_PAR"] = val

        if material in ["timber_frame", "timber_mass"]:
            parameters["IS_PAR"] = 1 if material == "timber_frame" else 2
            parameters["RO_PAR"] = 1 if material == "timber_frame" else 2
        else:
            parameters["IS_PAR"] = 0
            parameters["RO_PAR"] = 0

        return parameters

    def map_materials_to_parameters(self, extracted):
        parameters = {}

        mapping_keys = {
            "wall_material": ["EW_PAR", "IW_PAR"],
            "wall_insulation": ["EW_INS"],
            "roof_material": ["RO_PAR"],
            "roof_insulation": ["RO_INS"],
            "slab_material": ["IS_PAR"],
            "slab_insulation": ["ES_INS"]
        }

        for material_key, material_value in extracted.items():
            for param in mapping_keys.get(material_key, []):
                category = self.get_category_for_param(param)
                if category:
                    val = self.material_mappings[category].get(material_value.lower())
                    if val is not None:
                        parameters[param] = val

        return parameters

    def get_category_for_param(self, key):
        return {
            "EW_PAR": "Ext.Wall_Partition",
            "IW_PAR": "Int.Wall_Partition",
            "EW_INS": "Ext.Wall_Insulation",
            "RO_PAR": "Roof_Partition",
            "RO_INS": "Roof_Insulation",
            "IS_PAR": "Int.Slab_Partition",
            "ES_INS": "Ext.Slab_Insulation"
        }.get(key)

    def get_material_name(self, param_key, value):
        category = self.get_category_for_param(param_key)
        if category:
            return self.value_to_material[category].get(value, f"Unknown({value})")
        return f"Unknown({value})"
