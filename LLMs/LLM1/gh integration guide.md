"""
Complete Grasshopper Integration Guide

This guide explains how to set up the Python components in Grasshopper to integrate with your Flask LLM server.
Follow these steps to create the necessary components and connect them in your Grasshopper definition.
"""

# ========================
# SETUP INSTRUCTIONS
# ========================

"""
1. REQUIRED PYTHON PACKAGES

Before starting, make sure you have these Python packages installed in your Rhino/Grasshopper Python environment:
- requests
- json

You can install them using pip in the command line:
```
pip install requests
```
(json is included in the standard library)

2. COMPONENT OVERVIEW

The integration consists of four main Python components:

A. Conversation Component
   - Handles the chat interaction with the LLM
   - Maintains conversation state between runs
   - Collects the design parameters

B. Parameter Fetcher
   - Requests the complete parameter set from the Flask server
   - Prepares data for geometry generation

C. Geometry Generator
   - Creates 3D geometry based on design parameters
   - Handles different typologies (block, L-shape, U-shape, courtyard)
   - Calculates and returns metrics (GFA, aspect value)

D. Results Sender
   - Sends the geometric results back to the Flask server
   - Updates the ML parameters with the GH-generated geometric data

3. GRASSHOPPER SETUP

Here's how to set up your Grasshopper definition:
"""

# ========================
# CREATING THE COMPONENTS
# ========================

"""
For each Python component:

1. Add a new "Python Script" component to your Grasshopper canvas
2. Double-click to open the editor
3. Paste the corresponding code from the artifacts
4. Set up the inputs and outputs as described below
"""

# ========================
# CONVERSATION COMPONENT SETUP
# ========================

"""
INPUTS:
- input_text (string): Connect to a Panel or other text input source
- run (boolean): Connect to a Button or Toggle
- reset (boolean): Connect to a Button to reset the conversation

OUTPUTS:
- out (string): Connect to a Panel to display the LLM response
- state (string): Optional - connect to a Panel to monitor conversation state
- design_data (string): Optional - connect to a Panel to view collected parameters

HOW TO USE:
1. Type your building description in the text input
2. Toggle the 'run' button to send to the LLM
3. Continue the conversation by responding to LLM prompts
4. When design is complete, the state will change to 'complete'
"""

# ========================
# PARAMETER FETCHER SETUP
# ========================

"""
INPUTS:
- fetch (boolean): Connect to a Button or Toggle
- design_id (string, optional): Connect to a Panel if you want to fetch a specific design

OUTPUTS:
- json_data (string): Connect to the Geometry Generator input
- materiality (dictionary): Optional - connect to a Panel to view materiality parameters
- geometry_params (dictionary): Optional - connect to a Panel to view geometry parameters
- info (string): Connect to a Panel to display status information

HOW TO USE:
1. Once the conversation reaches 'complete' state, toggle the 'fetch' button
2. The component will request the complete parameter set from the Flask server
3. The output json_data will contain the parameters for geometry generation
"""

# ========================
# GEOMETRY GENERATOR SETUP
# ========================

"""
INPUTS:
- design_json (string): Connect to the json_data output from Parameter Fetcher
- run (boolean): Connect to a Button or Toggle

OUTPUTS:
- geometry (Rhino geometry): The generated 3D building model
- gfa (float): Gross floor area of the generated model
- av (float): Aspect value of the generated model
- info (string): Connect to a Panel to display status information

HOW TO USE:
1. Once parameters are fetched, toggle the 'run' button
2. The component will generate the appropriate geometry based on typology
3. Geometry will appear in the Rhino viewport
4. Metrics (GFA, aspect value) will be calculated and output
"""

# ========================
# COMPLETE WORKFLOW
# ========================

"""
Here's the complete workflow for using the integration:

1. User describes the building they want to create via the Conversation Component
2. LLM guides them through providing all necessary parameters
3. When the conversation is complete, user activates Parameter Fetcher
4. Design parameters are retrieved from the Flask server
5. User activates Geometry Generator to create the 3D model
6. Geometric metrics are calculated and sent back to the Flask server
7. The ML algorithm uses the complete parameter set (materiality + geometry)

TROUBLESHOOTING:

- Connection errors: Make sure your Flask server is running on port 5000
- Parameter errors: Check the Conversation Component state to ensure it reached 'complete'
- Geometry errors: Verify the parameter values in the json_data output
- Missing packages: Install required Python packages (requests, json)

EXTENDING THE SYSTEM:

- Add more typologies to the Geometry Generator
- Create additional Python components for specific tasks
- Add visualization elements for different material types
- Implement more detailed geometry creation based on WWR values
"""