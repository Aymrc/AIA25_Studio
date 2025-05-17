import json
from server.config import *
from server.keys import OPENAI_API_KEY

def classify_input(user_input: str) -> str:
    design_data = {
        "materials": ["concrete", "glass", "timber"],
        "embodied_carbon": "420 kgCO₂e/m²",
        "solar_radiation_area": "380 m²",
        "number_of_levels": 6,
        "typology": "block",
        "unit_counts": {
            "3BD": 8,
            "2BD": 12,
            "1BD": 10
        },
        "GFA": "2,400 m²",
        "plot_dimensions": "30m x 40m"
    }

    change_keywords = ["change", "replace", "switch", "update", "make it", "modify", "set", "turn into"]
    improve_keywords = ["improve", "reduce", "maximize", "minimize", "optimize", "should i", "could i", "recommend", "how can i"]

    lowered = user_input.lower()

    if any(kw in lowered for kw in change_keywords):
        return suggest_change(user_input, design_data)
    elif any(kw in lowered for kw in improve_keywords):
        return suggest_improvements(user_input, design_data)
    else:
        return answer_user_query(user_input, design_data)
    

def query_intro():
    """Prompt the user to ask about their design."""
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": """
                Greet the user briefly and say: "What would you like to know about your design?"
                Do not list options or explain functionality.
                """
            }
        ]
    )
    return response.choices[0].message.content


def answer_user_query(user_query, design_data):
    """Return a precise, factual answer using available project data."""
    design_data_json = json.dumps(design_data)
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": f"""
                You are a technical assistant. Answer the user's question using only this data:

                {design_data_json}

                Respond in 1–2 concise sentences. If the answer isn't in the data, say so directly.
                Avoid unnecessary explanations.
                """
            },
            {
                "role": "user",
                "content": user_query
            }
        ]
    )
    return response.choices[0].message.content


def suggest_improvements(user_prompt, design_data):
    """Give 1–2 brief, practical suggestions based on the design data."""
    design_data_json = json.dumps(design_data)
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": f"""
                You are a design advisor. Suggest practical improvements using this data:

                {design_data_json}

                Answer the user's prompt in 1–2 short, specific suggestions.
                Be direct. No intros, no conclusions. Do not repeat the user prompt.
                Only suggest changes relevant to this design.
                """
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )
    return response.choices[0].message.content


def suggest_change(user_prompt, design_data):
    """Interpret user's design change request and return a structured JSON output."""
    design_data_json = json.dumps(design_data)

    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": f"""
                You are a strict parser and design assistant.

                The user is requesting a design change. Based on the request and the project data below, output a JSON object in this format only:

                {{
                "action": "update", 
                "target": "<what should be changed>", 
                "new_value": "<what it should be changed to>", 
                "rationale": "<brief reason why this change could be beneficial>"
                }}

                Respond ONLY with a valid JSON object. Do not explain anything. Do not say "here is your response". Use the project data to inform your reasoning:

                {design_data_json}
"""
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )

    # Return parsed JSON for logging, or raw string for model
    return response.choices[0].message.content