import json
from server.config import *
from server.keys import OPENAI_API_KEY

def classify_input(user_input: str) -> str:
    """
    Basic intent classification based on keyword presence.
    Routes input to the right function using design_data.
    """
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

    keywords = ["improve", "reduce", "maximize", "minimize", "optimize", "should i", "could i", "recommend", "how can i"]

    if any(kw in user_input.lower() for kw in keywords):
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
