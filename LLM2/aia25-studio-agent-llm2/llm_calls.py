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
    """Interpret user's design change request and return a structured parameter dictionary."""
    design_data_text = json.dumps(design_data)

    system_prompt = f"""
        You are a design assistant. The user will request a design change. You must respond ONLY with a JSON object that represents a complete parameter configuration.

        ### Output format (mandatory structure):
        {{
            "ew_par": 0,
            "ew_ins": 0,
            "iw_par": 0,
            "es_ins": 1,
            "is_par": 0,
            "ro_par": 0,
            "ro_ins": 0,
            "wwr": 0.3,
            "gfa": 200.0,
            "av": 0.5
        }}

        ### Parameter definitions:

        - ew_par: Exterior Wall Partitions → BRICK=0, CONCRETE=1, EARTH=2, STRAW=3, TIMBER FRAME=4, TIMBER MASS=5  
        - ew_ins: Exterior Wall Insulation → CELLULOSE=0, CORK=1, EPS=2, GLASS WOOL=3, MINERAL WOOL=4, WOOD FIBER=5  
        - iw_par: Interior Wall Partitions → same as ew_par  
        - es_ins: Exterior Slabs Insulation → EXPANDED GLASS=0, XPS=1  
        - is_par: Interior Slabs → CONCRETE=0, TIMBER FRAME=1, TIMBER MASS=2  
        - ro_par: Roof Slabs → CONCRETE=0, TIMBER FRAME=1, TIMBER MASS=2  
        - ro_ins: Roof Insulation → CELLULOSE=0, CORK=1, EPS=2, EXPANDED GLASS=3, GLASS WOOL=4, MINERAL WOOL=5, WOOD FIBER=6, XPS=7  
        - wwr: Window-to-Wall Ratio → float (0.0–1.0)  
        - gfa: Gross Floor Area → float (no units)  
        - av: Air Volume → float

        ### Language alias mapping (user input to material index):
        - "wood" → TIMBER MASS (5)  
        - "wood frame" → TIMBER FRAME (4)  
        - "concrete" → CONCRETE (1)  
        - "brick" → BRICK (0)  
        - "earth" → EARTH (2)  
        - "straw" → STRAW (3)

        ### Output rules:
        - Respond with the full dictionary, even if the user only changes one thing.
        - Format gfa, wwr, av as floats (e.g., 4800.0). Do not return strings or include units.
        - No explanations. No extra text. Only JSON.

        ### Examples:

        If user says: “Change the material to wood”
        Respond:
        {{
        "ew_par": 5,
        "ew_ins": 0,
        "iw_par": 5,
        "es_ins": 1,
        "is_par": 2,
        "ro_par": 5,
        "ro_ins": 0,
        "wwr": 0.3,
        "gfa": 200.0,
        "av": 0.5
        }}

        If user says: “Change the GFA to 4800”
        Respond:
        {{
        "ew_par": 0,
        "ew_ins": 0,
        "iw_par": 0,
        "es_ins": 1,
        "is_par": 0,
        "ro_par": 0,
        "ro_ins": 0,
        "wwr": 0.3,
        "gfa": 4800.0,
        "av": 0.5
        }}

        Use this project data if relevant:
        {design_data_text}
        """

    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    return response.choices[0].message.content
