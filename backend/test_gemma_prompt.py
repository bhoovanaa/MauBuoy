from gemma_prompt import build_analysis_prompt

cv_output = {"health": "bleached", "confidence": 0.92}
sensor_data = {
    "water_temp_c": 29.8,
    "ph_level": 8.1,
    "salinity_ppt": 35.2,
    "turbidity_ntu": 2.1,
    "timestamp": "2026-07-28T10:30:00"
}

prompt = build_analysis_prompt(cv_output, sensor_data, "Blue Bay Marine Park")
print(prompt)