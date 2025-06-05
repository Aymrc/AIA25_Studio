def get_kpis(data, query=None):
    """Extracts and formats key performance indicators from the design state."""
    kpis = []

    # Extract a few common KPIs if they exist
    if 'GFA' in data:
        kpis.append(f"Gross Floor Area (GFA): {data['GFA']}")
    if 'embodied_carbon' in data:
        kpis.append(f"Embodied Carbon: {data['embodied_carbon']}")
    if 'number_of_levels' in data:
        kpis.append(f"Number of Levels: {data['number_of_levels']}")
    if 'solar_radiation_area' in data:
        kpis.append(f"Solar Radiation Area: {data['solar_radiation_area']}")
    if 'typology' in data:
        kpis.append(f"Typology: {data['typology']}")
    if 'carbon_Operational_Carbon_kgCO2e_per_m2a' in data:
        kpis.append(f"Operational Carbon: {data['carbon_Operational_Carbon_kgCO2e_per_m2a']} kgCO₂e/m²a")


    if not kpis:
        return "No KPI data available in current design context."

    return "\n".join(kpis)
