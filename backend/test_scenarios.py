"""Contract tests for the updated binary environmental model."""

import unittest

try:
    from .demo_scenarios import DEMO_SCENARIOS
    from .predict_risk import predict_bleaching_risk
except ImportError:
    from demo_scenarios import DEMO_SCENARIOS
    from predict_risk import predict_bleaching_risk


class UpdatedPredictionScenarioTests(unittest.TestCase):
    def _predict(self, scenario_key):
        scenario = DEMO_SCENARIOS[scenario_key]
        return predict_bleaching_risk(
            **scenario["prediction_input"],
            coral_health=scenario["cv_output"]["health"],
        )

    def test_expected_binary_predictions(self):
        for key, scenario in DEMO_SCENARIOS.items():
            with self.subTest(scenario=key):
                result = self._predict(key)
                self.assertEqual(
                    result["predicted_class"],
                    scenario["expected_prediction"],
                )
                self.assertEqual(
                    result["risk_level"],
                    scenario["expected_risk"],
                )

    def test_risk_increases_across_demo_scenarios(self):
        scores = [
            self._predict("scenario_1_healthy")["bleaching_risk_score"],
            self._predict("scenario_2_stressed")["bleaching_risk_score"],
            self._predict("scenario_3_bleached")["bleaching_risk_score"],
        ]
        self.assertLess(scores[0], scores[1])
        self.assertLess(scores[1], scores[2])

    def test_response_preserves_frontend_contract(self):
        result = self._predict("scenario_3_bleached")
        for field in (
            "probabilities",
            "predicted_class",
            "confidence",
            "bleaching_risk_score",
            "risk_level",
            "disease_outbreak_probability",
            "recovery_potential",
            "reasoning",
        ):
            self.assertIn(field, result)


if __name__ == "__main__":
    unittest.main()
