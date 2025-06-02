def generate_paths(data):
    """Suggests optioneering paths based on available design context."""
    typology = data.get("typology", "unspecified")
    options = [
        "Would you like to explore reducing embodied carbon?",
        "Shall I check if maximizing daylight might benefit this design?",
        "Do you want to compare the current GFA to a higher density version?"
    ]

    if typology == "block":
        options.append("Block typology detected — consider testing a courtyard layout for improved airflow.")
    elif typology == "courtyard":
        options.append("With a courtyard form, I can suggest optimizing solar access and shading.")

    return "\n".join(options)
