import unittest

from explainability_engine import (
    EXPLAINABILITY_VERSION,
    MODEL_VERSION,
    build_transfer_explanation,
)


SCORES = {
    "tactical": 88,
    "position": 92,
    "performance": 84,
    "proven": 80,
    "availability": 76,
    "potential": 72,
    "squad_need": 58,
    "deal_feasibility": 68,
    "league_strength": 95,
}

WEIGHTS = {
    "tactical": 21,
    "position": 13,
    "performance": 25,
    "proven": 12.5,
    "availability": 4,
    "potential": 4,
    "squad_need": 4,
    "deal_feasibility": 9,
    "league_strength": 7.5,
}


class ExplainabilityEngineTests(unittest.TestCase):
    def build_explanation(self, **overrides):
        values = {
            "player_name": "Example Player",
            "current_team": "Selling Club",
            "target_team": "Target Club",
            "role": "RW",
            "scores": SCORES,
            "weights": WEIGHTS,
            "final_score": 76.8,
            "expert_score": 80,
            "hybrid_weights": {
                "expert_model": 70,
                "historical_ml": 28.5,
                "club_role_ranker": 1.5,
            },
            "ml_prediction": {
                "success_forecast": 66,
                "success_percentile": 70,
                "confidence": "medium",
                "local_explanation": {
                    "positive_drivers": [
                        {"feature": "starts_before", "effect": 3.2},
                    ],
                    "risk_drivers": [
                        {"feature": "club_level_step", "effect": -2.4},
                    ],
                },
            },
            "ranker_prediction": {
                "club_role_rank_score": 60,
                "comparisons": 9,
                "confidence": "high",
            },
            "transfer_feasibility": {
                "eligible": True,
                "status": "plausible",
            },
            "budget_status": "within_budget",
            "value_source": "transfermarkt",
            "performance_reliability": 85,
            "context": "candidate_live_pool",
        }
        values.update(overrides)
        return build_transfer_explanation(**values)

    def test_candidate_trace_explains_all_three_engines(self):
        explanation = self.build_explanation()

        self.assertEqual(explanation["version"], EXPLAINABILITY_VERSION)
        self.assertEqual(explanation["model_version"], MODEL_VERSION)
        self.assertFalse(explanation["is_causal"])
        components = explanation["decision_trace"]["components"]
        self.assertEqual(
            [component["engine"] for component in components],
            ["expert_model", "historical_ml", "club_role_ranker"],
        )
        self.assertAlmostEqual(
            explanation["decision_trace"]["calculated_score"],
            76.8,
            places=1,
        )
        self.assertEqual(
            explanation["decision_trace"]["adjustments"],
            [],
        )

    def test_factors_and_ml_drivers_are_human_readable(self):
        explanation = self.build_explanation()

        self.assertTrue(explanation["positive_factors"])
        self.assertEqual(
            explanation["risk_factors"][0]["label"],
            "Squad need",
        )
        labels = {
            driver["label"] for driver in explanation["ml_drivers"]
        }
        self.assertIn("Pre-transfer starts", labels)
        self.assertIn("Club-level step", labels)
        self.assertIn("Target Club", explanation["summary"])

    def test_realism_guardrail_is_explicit(self):
        explanation = self.build_explanation(
            final_score=55,
            ranker_prediction=None,
            hybrid_weights={
                "expert_model": 70,
                "historical_ml": 30,
                "club_role_ranker": 0,
            },
            transfer_feasibility={
                "eligible": False,
                "status": "unrealistic",
            },
            context="isolated_player_analysis",
        )

        adjustments = explanation["decision_trace"]["adjustments"]
        self.assertEqual(adjustments[0]["type"], "realism_guardrail")
        self.assertTrue(
            any("ranker" in limitation for limitation in explanation["limitations"])
        )
        self.assertGreaterEqual(explanation["confidence"]["score"], 0)
        self.assertLessEqual(explanation["confidence"]["score"], 100)

    def test_missing_ml_uses_explicit_expert_fallback(self):
        explanation = self.build_explanation(
            final_score=80,
            expert_score=80,
            ml_prediction=float("nan"),
            ranker_prediction=float("nan"),
            hybrid_weights={"expert_model": 100},
        )

        components = explanation["decision_trace"]["components"]
        self.assertEqual(components[0]["weight"], 100)
        self.assertFalse(components[1]["available"])
        self.assertEqual(
            explanation["decision_trace"]["calculated_score"],
            80,
        )


if __name__ == "__main__":
    unittest.main()
