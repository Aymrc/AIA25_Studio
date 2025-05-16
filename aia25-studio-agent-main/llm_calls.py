from server.config import *
import json

def ask_single_parameter(param_name, instructions, examples, messages):
    prompt = f"Please provide the {param_name}. {instructions}\nExample: {examples}"
    
    while True:
        messages.append({"role": "assistant", "content": prompt})
        print("\n🤖 Copilot:", prompt)
        user_input = input("👤 You: ").strip()
        messages.append({"role": "user", "content": user_input})

        # Ask the LLM to extract the single parameter
        response = client.chat.completions.create(
            model=completion_model,
            messages=[
                {
                    "role": "system",
                    "content": f"""
You are an assistant that extracts the value of '{param_name}' from the user's input.
Return a JSON object like: {{ "{param_name}": "value" }}
If the value is unclear or invalid, return: {{ "{param_name}": null }}

Expected format:
- plot_size: two numbers in meters (e.g., "30x40", "30 by 40 meters")
- typology: block, courtyard, or l-shaped
- gfa: a number in square meters (e.g., "5000", "5000 m2")
- material: wood, steel, or concrete
"""
                },
                {"role": "user", "content": user_input}
            ]
        )

        try:
            result = json.loads(response.choices[0].message.content.strip())
            value = result.get(param_name)
            if value:
                return value
        except Exception as e:
            print("⚠️ Failed to parse LLM response:", e)

        print(f"⚠️ I couldn't understand the {param_name}. Please try again.\n")

def ask_until_all_complete(messages):
    plot_size = ask_single_parameter(
        "plot_size",
        "Enter the size of the plot in meters using two numbers (length by width).",
        "for example: 30 by 40 meters, 20 x 50",
        messages
    )

    typology = ask_single_parameter(
        "typology",
        "Choose from block, courtyard, or L-shaped.",
        "courtyard",
        messages
    )

    gfa = ask_single_parameter(
        "gfa",
        "State the gross floor area in square meters.",
        "5000 m2",
        messages
    )

    material = ask_single_parameter(
        "material",
        "Choose a preferred structural material: wood, steel, or concrete.",
        "concrete",
        messages
    )

    return plot_size, typology, gfa, material

def summarize_design(client, model, plot_size, typology, gfa, material):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a visionary architectural storyteller. Based on the user's building parameters, craft an evocative and imaginative summary of their proposed design. "
                    "Highlight the mood, spatial experience, and how the typology and materials express sustainability and design intent. Keep it brief, beautiful, and inspiring."
                )
            },
            {
                "role": "user",
                "content": f"The user provided the following: Typology = {typology}, Plot Size = {plot_size}, GFA = {gfa} m2, Material = {material}."
            }
        ]
    )
    return response.choices[0].message.content
