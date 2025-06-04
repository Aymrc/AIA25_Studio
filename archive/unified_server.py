from flask import Flask, request, jsonify
from flask.middleware.cors import CORSMiddleware
import json
import os
import time

from llm_calls import UnifiedLLMSystem
from utils.knowledge_compiler import KnowledgeCompiler

app = Flask(__name__)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize system components
llm_system = UnifiedLLMSystem()
knowledge_compiler = KnowledgeCompiler()

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Unified Copilot Server Running", "timestamp": time.time()})

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    """Main chat endpoint for material + WWR extraction"""
    try:
        data = request.get_json()
        user_input = data.get("message", "")
        
        if not user_input.strip():
            return jsonify({"response": "Please describe your building materials and window ratio."})
        
        # Process through unified LLM system
        response = llm_system.process_user_input(user_input)
        
        # Compile knowledge after each interaction
        knowledge_compiler.compile_all_data()
        
        return jsonify({"response": response})
        
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"})

@app.route("/knowledge", methods=["GET"])
def get_knowledge():
    """Get compiled knowledge data"""
    try:
        compiled_data = knowledge_compiler.get_compiled_data()
        return jsonify(compiled_data)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/rhino_data", methods=["POST"])
def receive_rhino_data():
    """Receive geometry data from Rhino monitor"""
    try:
        data = request.get_json()
        
        # Save to knowledge folder
        knowledge_file = os.path.join("knowledge", "rhino_geometry.json")
        os.makedirs("knowledge", exist_ok=True)
        
        with open(knowledge_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Recompile knowledge
        knowledge_compiler.compile_all_data()
        
        return jsonify({"status": "success", "message": "Rhino data received"})
        
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    print("🚀 Starting Unified Copilot Server on http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)