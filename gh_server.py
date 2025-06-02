from flask import Flask, request, jsonify
from server.config import *
from llm_calls import *
import traceback
import datetime

app = Flask(__name__)

# Global storage for geometry data (in production, use a proper database)
geometry_data_store = {
    "latest_geometry": None,
    "gfa": None,
    "compactness": None,
    "timestamp": None,
    "source": None  # "user" or "llm"
}

# Enable CORS to allow Grasshopper to connect
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

# Simple test endpoint
@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'ok', 'message': 'Server is running'})

@app.route('/llm_call', methods=['POST'])
def llm_call():
    try:
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
    except Exception as e:
        print(f"Error in llm_call: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'response': f"Server error: {str(e)}"}), 500

@app.route('/llm_message', methods=['POST'])
def llm_message():
    try:
        # Get the JSON data from the request
        data = request.get_json()
        
        # Extract input, state, and design data from the request
        input_string = data.get('input', '')
        state = data.get('state', 'initial')
        design_data = data.get('design_data', {})
        
        # Use the conversation state manager to handle the input
        try:
            new_state, response, updated_design_data = manage_conversation_state(state, input_string, design_data)
            
            # Check if we need to trigger IMMEDIATE geometry generation
            should_generate = (
                not updated_design_data.get("self_modeling", True) and 
                "geometry" in updated_design_data and 
                all(key in updated_design_data["geometry"] for key in ["typology", "number_of_levels", "width_m", "depth_m"]) and
                not updated_design_data.get("geometry_generated", False)
            )
            
            # If we should generate, mark it as generated to avoid duplicates
            if should_generate:
                updated_design_data["geometry_generated"] = True
                print(f"🎯 TRIGGERING IMMEDIATE GEOMETRY GENERATION")
                print(f"   Typology: {updated_design_data['geometry']['typology']}")
                print(f"   Levels: {updated_design_data['geometry']['number_of_levels']}")
                print(f"   Size: {updated_design_data['geometry']['width_m']}×{updated_design_data['geometry']['depth_m']}m")
            
            # Return a complete response with state and design data
            return jsonify({
                'response': response,
                'state': new_state,
                'design_data': updated_design_data,
                'trigger_geometry_generation': should_generate
            })
        except Exception as e:
            # If the conversation manager fails, fall back to basic Q&A
            print(f"Error in conversation state manager: {str(e)}")
            print(traceback.format_exc())
            
            # Fallback to simple Q&A
            response = answer_user_query(input_string, design_data)
            return jsonify({
                'response': response,
                'state': state,  # Keep the same state
                'design_data': design_data,  # Keep the same design data
                'trigger_geometry_generation': False
            })
            
    except Exception as e:
        # Handle any other errors
        print(f"Error in llm_message endpoint: {str(e)}")
        print(traceback.format_exc())
        
        return jsonify({
            'response': f"I'm sorry, an error occurred: {str(e)}",
            'state': 'error',
            'design_data': {},
            'trigger_geometry_generation': False
        }), 500

# File-based communication endpoint for Grasshopper
@app.route('/gh_input', methods=['GET'])
def gh_input():
    try:
        input_text = request.args.get('text', '')
        
        # Process the input
        response = answer_user_query(input_text, {})
        
        return jsonify({
            'status': 'success',
            'response': response
        })
    except Exception as e:
        print(f"Error in gh_input: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/prepare_materiality_json', methods=['POST'])
def prepare_materiality_json():
    """Prepare materiality JSON to send to ML algorithm"""
    try:
        data = request.get_json()
        design_data = data.get('design_data', {})
        
        # Generate materiality parameters based on material choice
        if 'materiality' in design_data:
            wwr = design_data.get('wwr', 0.3)
            
            # Create JSON structure for materiality parameters
            materiality_params = generate_materiality_json(design_data['materiality'], wwr)
            
            # Add geometry data if available
            if geometry_data_store["gfa"] is not None:
                materiality_params["gfa"] = geometry_data_store["gfa"]
            if geometry_data_store["compactness"] is not None:
                materiality_params["av"] = geometry_data_store["compactness"]
            
            return jsonify(materiality_params)
        else:
            return jsonify({'error': 'Missing materiality data'}), 400
    except Exception as e:
        print(f"Error in prepare_materiality_json: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/generate_geometry', methods=['POST'])
def generate_geometry():
    """Generate geometry parameters and send to Grasshopper for voxel modeling"""
    try:
        data = request.get_json()
        design_data = data.get('design_data', {})
        
        # Extract geometry parameters
        if 'geometry' in design_data:
            geometry = design_data['geometry']
            
            # Convert meters to voxels (divide by 3)
            width_voxels = geometry.get('width_m', 15) / 3
            depth_voxels = geometry.get('depth_m', 15) / 3
            
            geometry_params = {
                'typology': geometry.get('typology', 'block'),
                'width_voxels': int(width_voxels),
                'depth_voxels': int(depth_voxels), 
                'number_of_levels': geometry.get('number_of_levels', 4),
                'width_m': geometry.get('width_m', 15),
                'depth_m': geometry.get('depth_m', 15),
                'building_type': design_data.get('building_type', 'generic'),
                'source': 'llm'
            }
            
            print(f"Geometry parameters ready: {geometry_params}")
            
            return jsonify({
                'status': 'success', 
                'message': 'Geometry parameters ready for generation', 
                'parameters': geometry_params
            })
        else:
            return jsonify({'error': 'Missing geometry data'}), 400
    except Exception as e:
        print(f"Error in generate_geometry: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/send_geometry_data', methods=['POST'])
def send_geometry_data():
    """Receive geometry data (GFA, compactness) from Grasshopper"""
    try:
        data = request.get_json()
        
        # Store the geometry data
        geometry_data_store["gfa"] = data.get('gfa')
        geometry_data_store["compactness"] = data.get('compactness')
        geometry_data_store["timestamp"] = datetime.datetime.now().isoformat()
        geometry_data_store["source"] = data.get('source', 'unknown')
        
        return jsonify({
            'status': 'success',
            'message': 'Geometry data received and stored',
            'data': {
                'gfa': geometry_data_store["gfa"],
                'compactness': geometry_data_store["compactness"],
                'timestamp': geometry_data_store["timestamp"],
                'source': geometry_data_store["source"]
            }
        })
    except Exception as e:
        print(f"Error in send_geometry_data: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/get_geometry_data', methods=['GET'])
def get_geometry_data():
    """Get the latest geometry data"""
    try:
        if geometry_data_store["gfa"] is None:
            return jsonify({
                'status': 'no_data',
                'message': 'No geometry data available yet'
            })
        
        return jsonify({
            'status': 'success',
            'gfa': geometry_data_store["gfa"],
            'compactness': geometry_data_store["compactness"],
            'timestamp': geometry_data_store["timestamp"],
            'source': geometry_data_store["source"],
            'message': 'Latest geometry data retrieved'
        })
    except Exception as e:
        print(f"Error in get_geometry_data: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/set_self_modeling', methods=['POST'])
def set_self_modeling():
    """Update self_modeling status when user starts modeling"""
    try:
        data = request.get_json()
        self_modeling = data.get('self_modeling', True)
        
        return jsonify({
            'status': 'success',
            'message': f'Self-modeling set to {self_modeling}',
            'self_modeling': self_modeling
        })
    except Exception as e:
        print(f"Error in set_self_modeling: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/send_geometry_to_gh', methods=['POST'])
def send_geometry_to_gh():
    """Send geometry parameters to Grasshopper for modeling (legacy endpoint)"""
    try:
        data = request.get_json()
        design_data = data.get('design_data', {})
        
        # Extract geometry parameters
        if 'geometry' in design_data:
            geometry_data = {
                'typology': design_data['geometry'].get('typology', 'block'),
                'height': design_data['geometry'].get('height', 'mid-rise'),
                'number_of_levels': design_data['geometry'].get('number_of_levels', 4),
                'self_modeling': design_data.get('self_modeling', False),
                'building_type': design_data.get('building_type', 'generic')
            }
            
            return jsonify({
                'status': 'success', 
                'message': 'Geometry parameters sent to Grasshopper', 
                'parameters': geometry_data
            })
        else:
            return jsonify({'error': 'Missing geometry data'}), 400
    except Exception as e:
        print(f"Error in send_geometry_to_gh: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/get_gh_results', methods=['POST', 'GET'])
def get_gh_results():
    """Get geometry results back from Grasshopper (legacy endpoint)"""
    try:
        if request.method == 'POST':
            # Handle results posted from Grasshopper
            data = request.get_json()
            
            # Store the results
            geometry_data_store["gfa"] = data.get('gfa', 200.0)
            geometry_data_store["compactness"] = data.get('av', 0.5)
            geometry_data_store["timestamp"] = datetime.datetime.now().isoformat()
            geometry_data_store["source"] = data.get('source', 'grasshopper')
            
            return jsonify({
                'status': 'success',
                'message': 'Results received and stored'
            })
        else:
            # GET request - return the latest results
            return jsonify({
                'status': 'success',
                'gfa': geometry_data_store.get("gfa", 200.0),
                'av': geometry_data_store.get("compactness", 0.5),
                'message': 'Geometry successfully processed'
            })
    except Exception as e:
        print(f"Error in get_gh_results: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/get_current_conversation_state', methods=['GET'])
def get_current_conversation_state():
    """Get the current conversation state and design data"""
    try:
        # In a real implementation, you would retrieve the current conversation state
        # For now, we'll check if there's a stored state in temporary files (like your GH component does)
        
        import os
        temp_dir = os.path.join(os.environ.get('TEMP', '/tmp'), 'gh_design_assistant')
        state_file = os.path.join(temp_dir, 'current_state.txt')
        design_data_file = os.path.join(temp_dir, 'design_data.json')
        
        # Try to read the current state
        current_state = "initial"
        design_data = {}
        
        try:
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    current_state = f.read().strip()
            
            if os.path.exists(design_data_file):
                with open(design_data_file, 'r') as f:
                    import json
                    design_data = json.load(f)
                    
        except Exception as file_error:
            print(f"Error reading state files: {str(file_error)}")
        
        return jsonify({
            'status': 'success',
            'state': current_state,
            'design_data': design_data,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error in get_current_conversation_state: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/clear_geometry', methods=['POST'])
def clear_geometry():
    """Clear geometry endpoint - signals that geometry should be cleared"""
    try:
        data = request.get_json()
        print(f"🔄 Geometry clear signal received: {data}")
        
        # Store clear timestamp for reference
        clear_timestamp = datetime.datetime.now().isoformat()
        
        return jsonify({
            'status': 'success',
            'message': 'Geometry clear signal processed',
            'timestamp': clear_timestamp,
            'action': 'clear_geometry'
        })
    except Exception as e:
        print(f"Error in clear_geometry: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/geometry_cleared', methods=['POST'])
def geometry_cleared():
    """Acknowledge that geometry has been cleared by Grasshopper"""
    try:
        data = request.get_json()
        print(f"✅ Geometry cleared confirmation: {data}")
        
        return jsonify({
            'status': 'success',
            'message': 'Geometry clear confirmation received'
        })
    except Exception as e:
        print(f"Error in geometry_cleared: {str(e)}")
        return jsonify({'error': str(e)}), 500

# if __name__ == '__main__':
#     print("\n" + "="*50)
#     print("🚀 DESIGN ASSISTANT SERVER STARTING")
#     print("="*50)
#     print("📡 Server will be available at: http://127.0.0.1:5000")
#     print("🔗 Health check endpoint: http://127.0.0.1:5000/")
#     print("💬 Main LLM endpoint: http://127.0.0.1:5000/llm_message")
#     print("📐 Geometry generation: http://127.0.0.1:5000/generate_geometry")
#     print("🔄 Geometry clearing: http://127.0.0.1:5000/clear_geometry")
#     print("="*50)
    
#     # Bind to all interfaces so Grasshopper can connect
#     app.run(debug=True, host='0.0.0.0', port=5000)