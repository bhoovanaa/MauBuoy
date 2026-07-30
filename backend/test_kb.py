from restoration_knowledge_base import get_technique_recommendation

cv_output = {
    "health": "bleached",
    "confidence": 0.92
}

sensor_data = {
    "water_temp_c": 29.8,
    "turbidity_ntu": 2.1,
    "ph_level": 8.1
}

best = get_technique_recommendation(cv_output, sensor_data, "Blue Bay")
print(best)