"""Demo scenarios shared by prediction and restoration pipeline checks."""

DEMO_SCENARIOS = {
    "scenario_1_healthy": {
        "name": "Le Morne - Healthy Reef",
        "description": (
            "Healthy coral in low-stress conditions requiring preventive monitoring."
        ),
        "cv_output": {"health": "healthy", "confidence": 0.95},
        "prediction_input": {
            "latitude": -20.46,
            "longitude": 57.32,
            "depth_m": 18.0,
            "sst_celsius": 27.5,
            "dhw": 0.5,
        },
        "sensor_data": {
            "water_temp_c": 27.5,
            "ph_level": 8.2,
            "salinity_ppt": 35.5,
            "turbidity_ntu": 1.8,
            "depth_m": 18.0,
        },
        "location": "Le Morne",
        "expected_prediction": "No Bleaching",
        "expected_risk": "MODERATE",
        "expected_recommendation": "coral_gardening",
        "expected_alert": "LOW",
    },
    "scenario_2_stressed": {
        "name": "Balaclava - Early Thermal Stress",
        "description": (
            "Early warning conditions with visual stress and increasing heat exposure."
        ),
        "cv_output": {"health": "stressed", "confidence": 0.89},
        "prediction_input": {
            "latitude": -20.11,
            "longitude": 57.53,
            "depth_m": 8.0,
            "sst_celsius": 29.2,
            "dhw": 3.5,
        },
        "sensor_data": {
            "water_temp_c": 29.2,
            "ph_level": 7.9,
            "salinity_ppt": 34.8,
            "turbidity_ntu": 8.5,
            "depth_m": 8.0,
        },
        "location": "Balaclava",
        "expected_prediction": "Bleaching",
        "expected_risk": "HIGH",
        "expected_recommendation": "substrate_stabilization",
        "expected_alert": "MODERATE",
    },
    "scenario_3_bleached": {
        "name": "Blue Bay - Active Bleaching Event",
        "description": (
            "Active bleaching under severe accumulated heat stress requiring response."
        ),
        "cv_output": {"health": "bleached", "confidence": 0.93},
        "prediction_input": {
            "latitude": -20.44,
            "longitude": 57.72,
            "depth_m": 5.0,
            "sst_celsius": 31.2,
            "dhw": 8.5,
        },
        "sensor_data": {
            "water_temp_c": 31.2,
            "ph_level": 8.1,
            "salinity_ppt": 35.2,
            "turbidity_ntu": 2.1,
            "depth_m": 5.0,
        },
        "location": "Blue Bay",
        "expected_prediction": "Bleaching",
        "expected_risk": "CRITICAL",
        "expected_recommendation": "heat_resistant_outplanting",
        "expected_alert": "HIGH",
    },
}
