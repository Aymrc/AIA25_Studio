def classify_intent(user_input):
    lowered = user_input.lower()

    if any(kw in lowered for kw in ["change", "replace", "update", "modify", "set", "switch", "turn into"]):
        return "design_change"

    elif any(kw in lowered for kw in ["improve", "optimize", "minimize", "maximize", "reduce", "recommend", "should i", "could i", "how can i"]):
        return "suggestion"

    elif any(kw in lowered for kw in ["what", "how much", "how many", "show", "display", "list"]):
        return "data_query"

    elif lowered.strip() == "":
        return "fallback"

    else:
        return "unknown"
