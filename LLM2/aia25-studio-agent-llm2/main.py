from server.config import *
from llm_calls import *
import json

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

# Greet and ask open-ended query
print("\n👋 " + query_intro())

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
        print(result)

    elif any(kw in lowered for kw in improve_keywords):
        suggestion = suggest_improvements(user_input, design_data)
        print("\n🧩 Suggestion:")
        print(suggestion)

    else:
        reply = answer_user_query(user_input, design_data)
        print("\n📊 Data Insight:")
        print(reply)
