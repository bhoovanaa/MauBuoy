# roi_calculator.py (Build this FIRST - 20 min)

def calculate_restoration_roi(technique, health_status, stress_score):
    """
    Gemma 4 calls this to get accurate ROI numbers.
    """
    techniques = {
        "temporary_shading": {"base_survival": 70, "base_cost": 2500, "temp_sensitivity": 0.2},
        "coral_gardening": {"base_survival": 75, "base_cost": 10000, "temp_sensitivity": 0.8},
        "access_limit": {"base_survival": 55, "base_cost": 500, "temp_sensitivity": 0.4},
        "microfragmenting": {"base_survival": 72, "base_cost": 8000, "temp_sensitivity": 0.6},
        "heat_resistant_outplanting": {"base_survival": 85, "base_cost": 30000, "temp_sensitivity": 0.2},
        "substrate_stabilization": {"base_survival": 60, "base_cost": 25000, "temp_sensitivity": 0.3},
        "larval_propagation": {"base_survival": 40, "base_cost": 15000, "temp_sensitivity": 1.0},
        "no_intervention_monitoring": {"base_survival": 20, "base_cost": 2000, "temp_sensitivity": 0.1}
    }
    
    tech = techniques.get(technique, techniques["no_intervention_monitoring"])
    
    # Calculate adjusted survival rate
    survival = tech["base_survival"] - (stress_score * tech["temp_sensitivity"])
    if "bleached" in health_status.lower():
        survival -= 10
    survival = max(5, min(95, survival))
    
    return {
        "technique": technique,
        "predicted_survival_rate": f"{round(survival, 1)}%",
        "estimated_cost_usd": tech["base_cost"],
        "roi_score": round((survival / tech["base_cost"]) * 1000, 2)
    }
