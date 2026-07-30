"""Prompts for the Gemma 4 reef-analysis orchestrator."""

from __future__ import annotations

import json

try:
    from .restoration_knowledge_base import RESTORATION_TECHNIQUES
except ImportError:
    from restoration_knowledge_base import RESTORATION_TECHNIQUES


SYSTEM_PROMPT = """You are ReefGuardian AI, a decision-support assistant for coral
conservation teams in Mauritius.

Analyze the supplied visual assessment and environmental readings as independent
evidence. Preserve uncertainty and explicitly mention disagreements. Never claim
that the output is a field diagnosis.

Use the available tools to calculate environmental stress, bleaching risk, and
restoration ROI. Tool results are authoritative for numerical claims. Return 3
to 5 distinct, ranked intervention options from the supplied catalog. Give each
option a site-specific rationale, at least three implementation steps, and
caveats. Do not invent measurements, species, costs, survival rates, or field
observations. Recommendations must ask for marine-specialist review before
deployment. Write every JSON string as plain text. Do not use Markdown, LaTeX,
dollar-delimited math, backslash commands, or escaped percent signs.
"""


def build_analysis_prompt(
    cv_output: dict,
    sensor_data: dict,
    location_name: str,
) -> str:
    """Build a structured evidence package for Gemma 4."""

    readings = dict(sensor_data)
    if readings.get("sst_kelvin") is None and readings.get("water_temp_c") is not None:
        readings["sst_kelvin"] = float(readings["water_temp_c"]) + 273.15

    prediction_inputs_available = all(
        readings.get(field) is not None
        for field in ("latitude", "longitude", "depth_m", "sst_kelvin", "dhw")
    )
    evidence = {
        "location": location_name,
        "visual_assessment": cv_output,
        "environmental_readings": readings,
        "restoration_catalog": RESTORATION_TECHNIQUES,
    }
    prediction_instruction = (
        "Call the bleaching-risk tool using the supplied coordinates, depth, "
        "SST and DHW. "
        if prediction_inputs_available
        else "Bleaching-risk tool inputs are incomplete; do not invent them. "
    )
    return (
        "Analyze this ReefGuardian evidence package. Call the environmental "
        "stress tool before choosing a technique. "
        + prediction_instruction
        + "Call the "
        "restoration ROI tool for the selected technique. Retain any visual "
        "uncertainty or conflict in risk_factors.\n\n"
        + json.dumps(evidence, indent=2, default=str)
    )


if __name__ == "__main__":
    print(
        build_analysis_prompt(
            {"health": "Bleached", "confidence": 0.92, "status": "ok"},
            {
                "water_temp_c": 29.8,
                "ph_level": 8.1,
                "salinity_ppt": 35.2,
                "turbidity_ntu": 2.1,
                "latitude": -20.4,
                "longitude": 57.7,
                "depth_m": 5.0,
                "sst_kelvin": 302.95,
                "dhw": 4.5,
            },
            "Blue Bay Marine Park",
        )
    )
