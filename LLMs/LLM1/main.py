from server.config import *
from llm_calls import *
import json
import os
import shutil

print("\n\U0001F44B Hello! I'm your design assistant.")
print("I'll help you define early-stage building parameters like materials, climate, geometry, and more.")
print("Feel free to describe what you want to build — and I'll ask for anything else I need!\n")

# Folder for storing session iterations
SESSION_FOLDER = "design_iterations"

# Reset folder on start
if os.path.exists(SESSION_FOLDER):
    shutil.rmtree(SESSION_FOLDER)
os.makedirs(SESSION_FOLDER)

# Helper to append iteration files in the session
def save_design_iteration(data, count):
    filename = os.path.join(SESSION_FOLDER, f"iteration_{count}.json")
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\U0001F5C2️ Design parameters saved to {filename}")

# Begin interaction
messages = []
design_data = {}
iteration_count = 1

MANDATORY_KEYS = ["materiality", "climate", "wwr", "geometry.typology", "geometry.height"]

while True:
    user_input = input("\n📐 Describe your design idea, or just start with one aspect (e.g. 'a hotel made of wood'):\n> ")

    if user_input.lower() in ["exit", "quit"]:
        print("\U0001F44B Goodbye!")
        exit()

    messages.append({"role": "user", "content": user_input})
    design_data = collect_design_parameters(user_input, messages)

    # Check for missing mandatory fields
    missing = []
    for key in MANDATORY_KEYS:
        parts = key.split(".")
        ref = design_data
        for p in parts:
            ref = ref.get(p) if isinstance(ref, dict) else None
            if ref is None:
                missing.append(key)
                break

    if missing:
        missing_prompt = "\n".join(
            [f"Which value would you like to set for {m.replace('.', ' → ')}? If you're unsure, I can choose one for you." for m in missing]
        )
        print("\n❗ Missing parameters:")
        print(missing_prompt)
        continue
    else:
        save_design_iteration(design_data, iteration_count)
        iteration_count += 1
        break

# Enter follow-up Q&A loop
while True:
    user_input = input("\n💬 Would you like to ask anything or change something? (type 'exit' to quit)\n> ")

    if user_input.lower() in ["exit", "quit"]:
        print("\U0001F44B Goodbye!")
        break

    lowered = user_input.lower()
    change_keywords = ["change", "replace", "switch", "update", "make it", "modify", "set", "turn into"]
    improve_keywords = ["improve", "reduce", "maximize", "minimize", "optimize", "should i", "could i", "recommend", "how can i"]

    if any(kw in lowered for kw in change_keywords):
        result = suggest_change(user_input, design_data)
        print("\n🛠 Change Instruction:")
        print(result)
        # Update data if it's a valid JSON change
        try:
            change = json.loads(result)
            keys = change["target"].split(".")
            ref = design_data
            for k in keys[:-1]:
                ref = ref[k]
            ref[keys[-1]] = change["new_value"]
            save_design_iteration(design_data, iteration_count)
            iteration_count += 1
        except:
            pass

    elif any(kw in lowered for kw in improve_keywords):
        suggestion = suggest_improvements(user_input, design_data)
        print("\n🧩 Suggestion:")
        print(suggestion)

    else:
        reply = answer_user_query(user_input, design_data)
        print("\n📊 Data Insight:")
        print(reply)
