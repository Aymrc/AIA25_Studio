from flask import Flask, request, jsonify
from server.config import *
from llm_calls import *

app = Flask(__name__)

@app.route('/llm_call', methods=['POST'])
def llm_call():
    data = request.get_json()
    input_string = data.get('input', '').strip()

    if input_string.lower() in ["", "intro"]:
        return jsonify({'response': (
            "👋 Hello! I'm your design assistant.\n"
            "I'll help you define early-stage building parameters like materials, climate, geometry, and more.\n"
            "Feel free to describe what you want to build — and I'll ask for anything else I need!"
        )})

    response = classify_input(input_string)
    return jsonify({'response': response})


@app.route('/llm_message', methods=['POST'])
def llm_message():
    data = request.get_json()
    input_string = data.get('input', '')
    response = answer_user_query(input_string, {})
    return jsonify({'response': response})


if __name__ == '__main__':
    app.run(debug=True)
