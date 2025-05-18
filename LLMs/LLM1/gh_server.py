from flask import Flask, request, jsonify
from server.config import *
from llm_calls import *
import traceback

app = Flask(__name__)

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
        print(f"Received request data: {data}")
        
        # Extract input, state, and design data from the request
        input_string = data.get('input', '')
        state = data.get('state', 'initial')
        design_data = data.get('design_data', {})
        
        print(f"Processing message with state: {state}, input: '{input_string}'")
        
        # Use the conversation state manager to handle the input
        try:
            # This should use our conversation state management system
            new_state, response, updated_design_data = manage_conversation_state(state, input_string, design_data)
            
            print(f"New state: {new_state}")
            print(f"Response: {response[:50]}...")  # Print first 50 chars of response
            
            # Return a complete response with state and design data
            return jsonify({
                'response': response,
                'state': new_state,
                'design_data': updated_design_data
            })
        except Exception as e:
            # If the conversation manager fails, log the error and fall back to basic Q&A
            print(f"Error in conversation state manager: {str(e)}")
            import traceback
            print(traceback.format_exc())
            
            # Fallback to simple Q&A
            response = answer_user_query(input_string, design_data)
            return jsonify({
                'response': response,
                'state': state,  # Keep the same state
                'design_data': design_data  # Keep the same design data
            })
            
    except Exception as e:
        # Handle any other errors
        print(f"Error in llm_message endpoint: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        return jsonify({
            'response': f"I'm sorry, an error occurred: {str(e)}",
            'state': 'error',
            'design_data': {}
        }), 500

# File-based communication endpoint for Grasshopper
@app.route('/gh_input', methods=['GET'])
def gh_input():
    try:
        input_text = request.args.get('text', '')
        print(f"Received input from Grasshopper: {input_text}")
        
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
            
            return jsonify(materiality_params)
        else:
            return jsonify({'error': 'Missing materiality data'}), 400
    except Exception as e:
        print(f"Error in prepare_materiality_json: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/send_geometry_to_gh', methods=['POST'])
def send_geometry_to_gh():
    """Send geometry parameters to Grasshopper for modeling"""
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
    """Get geometry results back from Grasshopper (after processing)"""
    try:
        if request.method == 'POST':
            # Handle results posted from Grasshopper
            data = request.get_json()
            print(f"Received geometry results from GH: {data}")
            
            # In a real implementation, you would store these results
            # For now, just return success
            return jsonify({
                'status': 'success',
                'message': 'Results received and stored'
            })
        else:
            # GET request - return the latest results
            # In a real implementation, you would retrieve stored results
            # For now, return simulated results
            return jsonify({
                'status': 'success',
                'gfa': 200.0,  # Gross floor area
                'av': 0.5,     # Aspect value
                'message': 'Geometry successfully processed by Grasshopper'
            })
    except Exception as e:
        print(f"Error in get_gh_results: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Bind to all interfaces so Grasshopper can connect
    app.run(debug=True, host='0.0.0.0', port=5000)