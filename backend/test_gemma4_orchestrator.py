"""Contract tests for the Gemma 4 Ollama orchestration layer."""

import json
import unittest
from unittest.mock import patch

from .gemma_orchestrator import (
    GemmaUnavailableError,
    OLLAMA_RECOMMENDATION_SCHEMA,
    analyze_reef,
    call_gemma_with_tools,
    parse_gemma_response,
)


VALID_RECOMMENDATION = {
    "alert_level": "HIGH",
    "coral_health_summary": "Bleached coral was detected with strong confidence.",
    "environmental_assessment": "Temperature and accumulated heat are elevated.",
    "recommended_technique": "heat_resistant_outplanting",
    "technique_name": "Model supplied name",
    "reasoning": "Heat-adapted stock is the best fit, pending specialist review.",
    "predicted_survival_rate": "1%",
    "estimated_cost_per_hectare": "$1",
    "risk_factors": ["Elevated temperature", "Active bleaching"],
    "next_steps": ["Obtain marine-specialist review", "Start a limited pilot"],
    "confidence_score": 0.86,
    "interventions": [
        {
            "technique_id": "heat_resistant_outplanting",
            "rationale": "Best aligned with repeated thermal stress.",
            "implementation_steps": [
                "Verify nursery stock.",
                "Run a tagged pilot.",
                "Monitor through the next heat-stress period.",
            ],
            "caveats": ["Requires genetic-diversity safeguards."],
        },
        {
            "technique_id": "temporary_shading",
            "rationale": "Reduces acute light stress while longer-term work is prepared.",
            "implementation_steps": [
                "Map priority colonies.",
                "Install storm-safe shading.",
                "Monitor and remove after acute stress.",
            ],
            "caveats": ["Temporary measure only."],
        },
        {
            "technique_id": "access_limit",
            "rationale": "Reduces controllable local pressure during recovery.",
            "implementation_steps": [
                "Define an exclusion zone.",
                "Coordinate enforcement.",
                "Review water quality and compliance.",
            ],
            "caveats": ["Does not remove regional heat stress."],
        },
    ],
}


class Gemma4OrchestratorTests(unittest.TestCase):
    def test_structured_response_validation(self):
        parsed = parse_gemma_response(json.dumps(VALID_RECOMMENDATION))
        self.assertEqual(
            parsed["recommended_technique"],
            "heat_resistant_outplanting",
        )
        self.assertNotIn(
            "maxLength",
            json.dumps(OLLAMA_RECOMMENDATION_SCHEMA),
        )

    @patch("backend.gemma_orchestrator._ollama_chat")
    def test_tool_loop_uses_schema_constrained_final_call(self, chat):
        chat.side_effect = [
            {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "calculate_environmental_stress",
                                "arguments": {
                                    "water_temp_c": 31.2,
                                    "ph_level": 8.1,
                                    "turbidity_ntu": 2.1,
                                    "salinity_ppt": 35.2,
                                },
                            }
                        }
                    ],
                }
            },
            {"message": {"role": "assistant", "content": "Evidence collected."}},
            {
                "message": {
                    "role": "assistant",
                    "content": json.dumps(VALID_RECOMMENDATION),
                }
            },
        ]

        response = call_gemma_with_tools("Analyze this evidence.")
        self.assertEqual(json.loads(response)["alert_level"], "HIGH")
        self.assertIn("format", chat.call_args_list[-1].args[0])
        tool_messages = chat.call_args_list[1].args[0]["messages"]
        self.assertTrue(
            any(message.get("tool_name") for message in tool_messages)
        )

    @patch("backend.gemma_orchestrator._ollama_chat")
    def test_analysis_grounds_cost_and_survival_with_local_tools(self, chat):
        chat.side_effect = [
            {"message": {"role": "assistant", "content": "No tool call."}},
            {
                "message": {
                    "role": "assistant",
                    "content": json.dumps(VALID_RECOMMENDATION),
                }
            },
        ]
        result = analyze_reef(
            {"health": "Bleached", "confidence": 0.93, "status": "ok"},
            {
                "water_temp_c": 31.2,
                "ph_level": 8.1,
                "salinity_ppt": 35.2,
                "turbidity_ntu": 2.1,
                "latitude": -20.44,
                "longitude": 57.72,
                "depth_m": 5.0,
                "sst_kelvin": 304.35,
                "dhw": 8.5,
            },
            "Blue Bay",
        )
        self.assertEqual(result["estimated_cost_per_hectare"], "$30,000")
        self.assertNotEqual(result["predicted_survival_rate"], "1%")
        self.assertEqual(result["model"], "gemma4")
        self.assertGreaterEqual(len(result["interventions"]), 3)
        self.assertGreater(
            result["interventions"][0]["baseline_risk_score"],
            result["interventions"][0]["projected_risk_score"],
        )

    @patch("backend.gemma_orchestrator._ollama_chat")
    def test_unavailable_ollama_returns_error_for_api_fallback(self, chat):
        chat.side_effect = GemmaUnavailableError("Ollama unavailable")
        result = analyze_reef(
            {"health": "Healthy", "confidence": 0.9},
            {
                "water_temp_c": 27.5,
                "ph_level": 8.2,
                "salinity_ppt": 35.5,
                "turbidity_ntu": 1.8,
            },
            "Le Morne",
        )
        self.assertEqual(result["alert_level"], "ERROR")
        self.assertIn("Ollama unavailable", result["reasoning"])


if __name__ == "__main__":
    unittest.main()
