import json
from server.config import *

# === CLASSIFICATION CALL FOR RAW TEXT > STRUCTURED PARAMS ===
def classify_input(user_input):
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": """
You are an assistant that extracts architectural design parameters from user input.

Your task is to return a JSON object with the following format. ONLY fill in fields the user explicitly mentions. For anything unclear or missing, just omit the field.

Return exactly this format:

{
  "materiality": "<string>",
  "climate": "<hot-humid | cold | arid | temperate>",
  "wwr": <float>,
  "geometry": {
    "typology": "<courtyard | block | L-shape | U-shape>",
    "height": "<low-rise | mid-rise | high-rise>",
    "number_of_levels": <int>
  }
}

Only output a valid JSON object. Do not add extra text.
"""
            },
            {"role": "user", "content": user_input}
        ]
    )

    return response.choices[0].message.content


# === QUERY INTRO ===
def query_intro():
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Introduce yourself as a design assistant. Explain that you will help collect "
                    "basic architectural parameters such as materiality, climate, WWR, and geometry, "
                    "to feed a generative ML prediction engine."
                )
            }
        ]
    )
    return response.choices[0].message.content.strip()

# === STRUCTURED PARSING ===
def collect_design_parameters(user_input, messages):
    try:
        raw = classify_input(user_input)
        return json.loads(raw)
    except Exception as e:
        return None

# === CHANGE SUGGESTIONS ===
def suggest_change(user_prompt, design_data):
    design_data_json = json.dumps(design_data)
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": f"""
You are a structured assistant. The user wants to change something in this building design:

{design_data_json}

Respond ONLY with a JSON object:
{{
  "action": "update",
  "target": "<parameter_to_change>",
  "new_value": "<desired_value>",
  "rationale": "<why it's a good change>"
}}
"""
            },
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content

# === IMPROVEMENT SUGGESTIONS ===
def suggest_improvements(user_prompt, design_data):
    design_data_json = json.dumps(design_data)
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": f"""
Suggest 1–2 creative improvements based on this building design (JSON below).
Be specific and helpful. Avoid boilerplate or obvious suggestions.

{design_data_json}
"""
            },
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content

# === GENERAL Q&A ===
def answer_user_query(user_prompt, design_data):
    design_data_json = json.dumps(design_data)
    response = client.chat.completions.create(
        model=completion_model,
        messages=[
            {
                "role": "system",
                "content": f"""
Answer the user's design question using the following data:

{design_data_json}

Keep it friendly and informative. Do NOT mention legal restrictions, codes, or impossibilities.
If information is missing, kindly ask the user to provide it.
"""
            },
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content
