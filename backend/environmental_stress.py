# environmental_stress.py (Build this SECOND - 15 min)

def calculate_environmental_stress(water_temp_c, ph_level, turbidity_ntu, salinity_ppt):
    """
    Gemma 4 calls this to understand environmental conditions.
    """
    stress_score = 0
    
    if water_temp_c > 29.0:
        stress_score += min((water_temp_c - 29.0) * 15, 30)
    if ph_level < 8.0:
        stress_score += min((8.0 - ph_level) * 50, 25)
    if turbidity_ntu > 5.0:
        stress_score += min((turbidity_ntu - 5.0) * 5, 25)
    
    return {
        "stress_score": round(stress_score, 1),
        "stress_level": "LOW" if stress_score < 25 else "MODERATE" if stress_score < 50 else "HIGH" if stress_score < 75 else "CRITICAL"
    }