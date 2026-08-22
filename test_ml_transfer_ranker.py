import json
import unittest
from pathlib import Path

from ml.transfer_ranker_engine import (
    load_ranker_bundle,
    rank_feature_rows,
    ranker_status,
)
from ml.transfer_success_engine import build_feature_row


ROOT = Path(__file__).resolve().parent
METADATA_PATH = ROOT / "models/transfer_ranker_v1_metadata.json"


class TransferRankerModelTests(unittest.TestCase):
    def test_tracked_ranker_artifact_loads(self):
        bundle = load_ranker_bundle()
        self.assertIsNotNone(bundle)
        self.assertTrue(ranker_status()["available"])
        self.assertEqual(
            bundle["version"],
            "transfer-ranker-pairwise-hgb-v1",
        )

    def test_pairwise_model_and_conservative_blend_beat_chance(self):
        metadata = json.loads(
            METADATA_PATH.read_text(encoding="utf-8")
        )
        model = metadata["test_metrics"]
        baseline = metadata["pointwise_baseline_metrics"]
        combined = metadata["combined_test_metrics"]

        self.assertGreater(model["pairwise_auc"], 0.5)
        self.assertGreater(model["pairwise_accuracy"], 0.5)
        self.assertGreater(metadata["samples"]["test_pairs"], 3000)
        self.assertGreaterEqual(
            combined["ndcg_at_10"],
            baseline["ndcg_at_10"],
        )

    def test_live_pairwise_scores_are_aligned_and_bounded(self):
        kane = build_feature_row(
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
        lautaro = build_feature_row(
            transfermarkt_player_id=406625,
            current_team="Inter",
            target_team="Barcelona",
            current_league="Serie A",
            target_league="La Liga",
            age=28,
            market_value_m_eur=85,
            appearances=45,
            starts=39,
            minutes=3500,
            goals=23,
            assists=6,
            primary_position="ST",
        )

        self.assertIsNotNone(kane)
        self.assertIsNotNone(lautaro)
        scores = rank_feature_rows([kane, lautaro])
        self.assertEqual(len(scores), 2)
        for score in scores:
            self.assertGreaterEqual(score["club_role_rank_score"], 0)
            self.assertLessEqual(score["club_role_rank_score"], 100)
            self.assertEqual(score["comparisons"], 1)
            self.assertTrue(score["relative_to_live_pool"])
        self.assertAlmostEqual(
            scores[0]["club_role_rank_score"]
            + scores[1]["club_role_rank_score"],
            100.0,
            places=1,
        )


if __name__ == "__main__":
    unittest.main()
