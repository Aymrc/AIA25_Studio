from server.config import client, completion_model
from llm_calls import ask_until_all_complete, summarize_design

# === Introduction printed manually ===
print("\n🤖 Copilot: Hello! I'm your architectural design assistant.")
print("🤖 Copilot: I’ll help you make early design decisions based on sustainability KPIs like embodied carbon and thermal performance.\n")
print("To begin, I’ll ask you a few questions one by one to define your project:\n")
print(" - 📏 Plot size (e.g., 30 by 40 meters)")
print(" - 🧱 Typology: Block, Courtyard, or L-shaped")
print(" - 🏢 Gross Floor Area (GFA) in square meters")
print(" - 🧱 Structural material: Wood, Steel, or Concrete\n")

# === Initialize message history ===
messages = [
    {
        "role": "system",
        "content": (
            "You are an architectural design copilot. Your role is to ask the user for four parameters one by one: "
            "plot size, typology, GFA, and structural material. After collecting all inputs, you will summarize their "
            "design in a creative and architectural tone."
        )
    }
]

# === Input collection step-by-step ===
plot_size, typology, gfa, structure_material = ask_until_all_complete(messages)

# === Final summary generation ===
summary = summarize_design(client, completion_model, plot_size, typology, gfa, structure_material)

# === Output ===
print("\n🏗️ Project Summary:\n" + summary)
