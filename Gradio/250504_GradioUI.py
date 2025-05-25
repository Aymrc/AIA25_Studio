import gradio as gr

# Carbon performance feedback
def carbon_feedback(material):
    feedback_map = {
        "Concrete": "Concrete has a high carbon footprint. Consider using recycled aggregates.",
        "Steel": "Steel is energy-intensive. Prefer reused or low-carbon steel.",
        "Wood": "Wood is low-carbon if sustainably sourced.",
        "Mixed": "Mixed materials need optimization to reduce emissions."
    }
    return feedback_map.get(material, "Select a material to get feedback.")

# Update preview panel
def update_preview(selection):
    return f"{selection} content shown here."

# LLM chat response
def respond(message, history):
    response = f"LLM: Got it. You said: '{message}'"
    history.append((message, response))
    return "", history

with gr.Blocks() as demo:
    gr.Markdown("### Gradio user interface")

    with gr.Tab("DESIGN SPACE"):
        with gr.Row(equal_height=True):
            # LEFT PANEL
            with gr.Column(scale=1):
                with gr.Group():
                    gr.Markdown("**INITIAL INPUTS PANEL**")
                    gr.File(label="Upload model", height=280)  # Increased height
                    gr.Textbox(label="Climate type", value="Tropical", interactive=False)
                    material = gr.Dropdown(["Concrete", "Steel", "Wood", "Mixed"], label="Material selection")

            # CENTER PANEL
            with gr.Column(scale=2):
                with gr.Group():
                    gr.Markdown("**BUILDING PREVIEW PANEL**")
                    view_choice = gr.Radio(["Model Preview", "Render Preview"], label="Preview mode", value="Model Preview")
                    view_display = gr.Textbox(label="", lines=22, interactive=False)
                    view_choice.change(fn=update_preview, inputs=view_choice, outputs=view_display)

            # RIGHT PANEL
            with gr.Column(scale=1):
                with gr.Group():
                    gr.Markdown("**CARBON PERFORMANCE PANEL**")
                    carbon_output = gr.Textbox(value="Live feedback on carbon performance & improvement strategies", lines=5, interactive=False)
                    material.change(fn=carbon_feedback, inputs=material, outputs=carbon_output)

                with gr.Group():
                    gr.Markdown("**LLM COMMUNICATION PANEL**")
                    chatbot = gr.Chatbot(label="LLM Assistant", height=230)
                    msg = gr.Textbox(label="Message", placeholder="Ask for design changes...")
    
        # BOTTOM ROW: aligned buttons
        with gr.Row():
            with gr.Column(scale=1):
                gr.Button("DOWNLOAD MODEL")
            with gr.Column(scale=2):
                pass  # Center column empty for alignment
            with gr.Column(scale=1):
                send = gr.Button("Send")
                send.click(fn=respond, inputs=[msg, chatbot], outputs=[msg, chatbot])

    gr.Tab("VERSIONS")
    gr.Tab("CARBON INFO")
    gr.Tab("USER INSTRUCTIONS")
    gr.Tab("UNDER THE HOOD")

demo.launch()
