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
            "Let's start by discussing what you'd like to build!"
        )})

    response = classify_input(input_string)
    return jsonify({'response': response})


@app.route('/llm_message', methods=['POST'])
def llm_message():
    data = request.get_json()
    input_string = data.get('input', '')
    
    # Get conversation state if available
    state = data.get('state', 'initial')
    design_data = data.get('design_data', {})
    
    # Manage the conversation based on the state
    new_state, response, updated_design_data = manage_conversation_state(state, input_string, design_data)
    
    # Return response with updated state and design data
    return jsonify({
        'response': response,
        'state': new_state,
        'design_data': updated_design_data
    })


@app.route('/prepare_materiality_json', methods=['POST'])
def prepare_materiality_json():
    """Prepare materiality JSON to send to ML algorithm"""
    data = request.get_json()
    design_data = data.get('design_data', {})
    
    # Generate materiality parameters based on material choice
    if 'materiality' in design_data:
        wwr = design_data.get('wwr', 0.3)
        
        # Create JSON structure exactly as shown in diagram image 2
        materiality_params = generate_materiality_json(design_data['materiality'], wwr)
        
        # Return just the materiality and WWR for now, as specified
        return jsonify(materiality_params)
    else:
        return jsonify({'error': 'Missing materiality data'}), 400


@app.route('/send_geometry_to_gh', methods=['POST'])
def send_geometry_to_gh():
    """Send geometry parameters to Grasshopper for modeling"""
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
        
        # This would connect to the Grasshopper server
        # For now, we'll just simulate and return success
        
        # In a real implementation, this might look like:
        # response = requests.post('http://localhost:8080/run_grasshopper', json=geometry_data)
        # return jsonify(response.json())
        
        return jsonify({
            'status': 'success', 
            'message': 'Geometry parameters sent to Grasshopper', 
            'parameters': geometry_data
        })
    else:
        return jsonify({'error': 'Missing geometry data'}), 400


@app.route('/get_gh_results', methods=['GET'])
def get_gh_results():
    """Get geometry results back from Grasshopper (after processing)"""
    # In a real implementation, this would retrieve results from a database or file
    # where Grasshopper would have saved them
    
    # For now, return a simple simulated result
    return jsonify({
        'status': 'success',
        'gfa': 200.0,  # Gross floor area
        'av': 0.5,     # Aspect value
        'message': 'Geometry successfully processed by Grasshopper'
    })


if __name__ == '__main__':
    app.run(debug=True)