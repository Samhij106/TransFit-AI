import unittest

import pandas as pd

from age_potential_engine import calculate_potential
from audit_player_analysis_data import audit_player_data
from performance_fit_engine import (
    PERFORMANCE_WEIGHTS,
    calculate_percentiles,
    calculate_performance_score,
)


class PerformanceOutlierTests(unittest.TestCase):
    def _players(self):
        metrics = {
            metric
            for weights in PERFORMANCE_WEIGHTS.values()
            for metric in weights
        }
        rows = []

        for player_id, attempts, successes, raw_rate in (
            (1, 1, 1, 100.0),
            (2, 100, 60, 60.0),
            (3, 100, 30, 30.0),
        ):
            row = {
                "player_id": player_id,
                "name": f"Player {player_id}",
                "position_group": "FB",
                "minutes": 1800,
                "dribble_attempts": attempts,
                "successful_dribbles": successes,
                "dribble_success_rate": raw_rate,
                "shots": 0,
                "shots_on_target": 0,
                "shot_accuracy": 0,
            }
            for metric in metrics:
                row.setdefault(metric, 1.0)
            rows.append(row)

        return pd.DataFrame(rows)

    def test_tiny_perfect_sample_is_shrunk_before_ranking(self):
        players = calculate_percentiles(self._players())
        tiny = players.loc[players["player_id"] == 1].iloc[0]
        stable = players.loc[players["player_id"] == 2].iloc[0]

        self.assertEqual(tiny["dribble_success_rate"], 100.0)
        self.assertLess(
            tiny["dribble_success_rate_model_value"],
            60.0,
        )
        self.assertLess(
            tiny["dribble_success_rate_pct"],
            stable["dribble_success_rate_pct"],
        )

    def test_explanation_keeps_raw_and_sample_aware_values(self):
        players = calculate_percentiles(self._players())
        result = calculate_performance_score(players.iloc[0])
        detail = result["details"].loc[
            result["details"]["metric"]
            == "dribble_success_rate"
        ].iloc[0]

        self.assertEqual(detail["raw_value"], 100.0)
        self.assertEqual(detail["sample_size"], 1)
        self.assertLess(detail["model_value"], 60.0)

    def test_repository_dataset_has_no_hard_data_errors(self):
        report = audit_player_data()

        self.assertEqual(report["hard_error_count"], 0)
        self.assertEqual(report["relationship_error_count"], 0)
        self.assertGreater(report["missing_value_count"], 0)

    def test_missing_age_uses_neutral_finite_potential(self):
        result = calculate_potential(pd.Series({
            "age": None,
            "age_band": "unknown",
            "performance_score": 70.0,
            "performance_for_age": 60.0,
        }))

        self.assertIsNone(result["age"])
        self.assertEqual(result["development_runway"], 50.0)
        self.assertGreaterEqual(result["potential_score"], 0)
        self.assertLessEqual(result["potential_score"], 100)


if __name__ == "__main__":
    unittest.main()
