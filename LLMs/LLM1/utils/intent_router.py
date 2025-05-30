def classify_intent(user_input):
    """Enhanced intent classification for material + WWR extraction"""
    lowered = user_input.lower()
    
    # Material + WWR specification keywords
    material_keywords = [
        "brick", "concrete", "earth", "straw", "timber", "wood",
        "insulation", "cork", "cellulose", "eps", "wall", "roof", "slab",
        "window", "glazing", "glass", "%", "percent", "ratio"
    ]
    
    if any(keyword in lowered for keyword in material_keywords):
        return "design_change"
    
    # Change/update keywords
    if any(kw in lowered for kw in ["change", "replace", "update", "modify", "set", "switch"]):
        return "design_change"
    
    # Data query keywords  
    if any(kw in lowered for kw in ["what", "how much", "show", "display", "current", "status"]):
        return "data_query"
    
    # Suggestion keywords (dormant for now)
    if any(kw in lowered for kw in ["improve", "optimize", "suggest", "recommend"]):
        return "suggestion"
    
    return "unknown"