"""Lightweight contract checks that do not load the CV checkpoints."""

import unittest

try:
    from .cv_model import VISION_SERVICE
    from .fusion import (
        deterministic_recommendation,
        fuse_assessments,
        normalize_visual_assessment,
    )
except ImportError:
    from cv_model import VISION_SERVICE
    from fusion import (
        deterministic_recommendation,
        fuse_assessments,
        normalize_visual_assessment,
    )


class IntegrationContractTests(unittest.TestCase):
    def test_model_artifacts_are_discoverable(self):
        status = VISION_SERVICE.model_status()
        self.assertTrue(status["yolo"]["available"])
        self.assertTrue(status["sam_vit_b"]["available"])
        self.assertFalse(status["yolo"]["loaded"])

    def test_uncertain_visual_state_is_preserved(self):
        normalized = normalize_visual_assessment(
            {
                "status": "no_reliable_coral_detected",
                "overall_condition": "Uncertain",
                "confidence": 0,
            }
        )
        self.assertEqual(normalized["health"], "Uncertain")
        self.assertEqual(normalized["status"], "no_reliable_coral_detected")

    def test_fusion_flags_model_disagreement(self):
        result = fuse_assessments(
            {"overall_condition": "Healthy", "confidence": 0.82, "status": "ok"},
            {"bleaching_risk_score": 87, "risk_level": "CRITICAL"},
        )
        self.assertTrue(result["review_required"])
        self.assertIn(
            "healthy_visual_but_high_environmental_risk",
            result["review_flags"],
        )

    def test_recommendation_has_safe_fallback_contract(self):
        result = deterministic_recommendation(
            {"overall_condition": "Bleached", "confidence": 0.82, "status": "ok"},
            {
                "water_temp_c": 29.8,
                "ph_level": 8.1,
                "salinity_ppt": 35.2,
                "turbidity_ntu": 2.1,
            },
            "Blue Bay Marine Park",
        )
        self.assertIn(result["alert_level"], {"HIGH", "CRITICAL"})
        self.assertEqual(
            result["recommendation_source"],
            "deterministic_threshold_engine",
        )
        self.assertIn("decision_support_disclaimer", result)
        self.assertGreaterEqual(len(result["interventions"]), 3)
        for intervention in result["interventions"]:
            self.assertLessEqual(
                intervention["projected_risk_score"],
                intervention["baseline_risk_score"],
            )
            self.assertGreaterEqual(len(intervention["implementation_steps"]), 3)


if __name__ == "__main__":
    unittest.main()
