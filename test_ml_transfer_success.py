import json
import unittest
from pathlib import Path

from ml.model_config import FEATURES
from ml.transfer_success_engine import (
    HYBRID_SCORE_VERSION,
    build_feature_row,
    hybrid_score,
    load_model_bundle,
    model_status,
    predict_feature_rows,
)


ROOT = Path(__file__).resolve().parent
METADATA_PATH = ROOT / "models/transfer_success_v1_metadata.json"


class TransferSuccessModelTests(unittest.TestCase):
    def test_tracked_model_artifacts_load(self):
        bundle = load_model_bundle()
        self.assertIsNotNone(bundle)
        self.assertEqual(bundle["features"], FEATURES)
        self.assertEqual(
            model_status()["hybrid_version"],
            HYBRID_SCORE_VERSION,
        )

    def test_held_out_model_beats_naive_baseline(self):
        metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
        model = metadata["test_metrics"]
        baseline = metadata["baseline_metrics"]

        self.assertLess(model["mae"], baseline["mae"])
        self.assertLess(model["rmse"], baseline["rmse"])
        self.assertGreater(model["ndcg_at_10"], baseline["ndcg_at_10"])
        self.assertGreater(model["success_auc"], baseline["success_auc"])
        self.assertGreater(metadata["samples"]["test"], 1000)

    def test_feature_builder_and_prediction_are_bounded(self):
        row = build_feature_row(
            transfermarkt_player_id=132098,
            current_team="Bayern München",
            target_team="Barcelona",
            current_league="Bundesliga",
            target_league="La Liga",
            age=32,
            market_value_m_eur=60,
            appearances=48,
            starts=43,
            minutes=3900,
            goals=41,
            assists=8,
            primary_position="ST",
        )

        self.assertIsNotNone(row)
        self.assertEqual(list(row), FEATURES)
        prediction = predict_feature_rows(
            [row],
            include_explanations=True,
        )[0]
        self.assertGreaterEqual(prediction["success_forecast"], 0)
        self.assertLessEqual(prediction["success_forecast"], 100)
        self.assertGreaterEqual(prediction["success_percentile"], 0)
        self.assertLessEqual(prediction["success_percentile"], 100)
        self.assertIn(prediction["confidence"], {"low", "medium", "high"})
        explanation = prediction["local_explanation"]
        self.assertFalse(explanation["is_causal"])
        self.assertGreater(
            len(explanation["positive_drivers"])
            + len(explanation["risk_drivers"]),
            0,
        )

    def test_hybrid_uses_historical_percentile_and_safe_fallback(self):
        prediction = {"success_percentile": 80.0}
        self.assertEqual(hybrid_score(70.0, prediction), 73.0)
        self.assertEqual(hybrid_score(70.0, None), 70.0)


if __name__ == "__main__":
    unittest.main()
