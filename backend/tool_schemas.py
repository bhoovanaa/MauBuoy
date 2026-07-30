# tool_schemas.py
"""
Function schemas for Gemma 4 tool calling.
Your friend will use these to configure Gemma 4's available tools.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_environmental_stress",
            "description": "Calculates overall environmental stress score (0-100) and identifies the primary stressor affecting coral health.",
            "parameters": {
                "type": "object",
                "properties": {
                    "water_temp_c": {"type": "number", "description": "Water temperature in Celsius"},
                    "ph_level": {"type": "number", "description": "pH level of water"},
                    "turbidity_ntu": {"type": "number", "description": "Turbidity in NTU"},
                    "salinity_ppt": {"type": "number", "description": "Salinity in parts per thousand"}
                },
                "required": ["water_temp_c", "ph_level", "turbidity_ntu", "salinity_ppt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_restoration_roi",
            "description": "Calculates predicted ROI (survival rate, cost, time) for a specific restoration technique given current conditions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "technique": {
                        "type": "string",
                        "enum": ["temporary_shading", "coral_gardening", "access_limit", "microfragmenting", "substrate_stabilization", "heat_resistant_outplanting", "larval_propagation", "no_intervention_monitoring"]
                    },
                    "health_status": {"type": "string", "enum": ["healthy", "stressed", "bleached", "dead", "uncertain", "unknown"]},
                    "stress_score": {"type": "number", "description": "Environmental stress score 0-100"}
                },
                "required": ["technique", "health_status", "stress_score"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "predict_14_day_bleaching_risk",
            "description": "Predicts 14-day risks (bleaching, disease, mortality) based on environmental data AND current coral health state.",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"},
                    "depth": {"type": "number"},
                    "sst_kelvin": {"type": "number"},
                    "dhw": {"type": "number"},
                    "coral_health": {
                        "type": "string",
                        "enum": ["healthy", "stressed", "bleached", "dead", "unknown"],
                        "description": "Current coral health state from CV model"
                    }
                },
                "required": ["latitude", "longitude", "depth", "sst_kelvin", "dhw", "coral_health"]
            }
        }
    }
]
