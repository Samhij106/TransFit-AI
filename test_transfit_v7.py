import unittest

from realistic_data_engine import (
    blend_performance_score,
    calibrate_proven_level,
)
from transfer_fit_v5 import SCORE_WEIGHTS
from transfit_service import (
    compare_players,
    search_players,
)


class TransFitV7RegressionTests(unittest.TestCase):
    def test_score_weights_total_one_hundred(self):
        self.assertEqual(
            sum(SCORE_WEIGHTS.values()),
            100,
        )
        self.assertEqual(
            SCORE_WEIGHTS["availability"],
            5,
        )

    def test_attacking_output_has_less_influence_on_dm(self):
        forward_score = blend_performance_score(
            league_performance_score=70,
            production_score=100,
            position_group="FW",
        )
        defensive_midfield_score = blend_performance_score(
            league_performance_score=70,
            production_score=100,
            position_group="DM",
        )

        self.assertEqual(forward_score, 85)
        self.assertEqual(defensive_midfield_score, 73)

    def test_market_peer_signal_blocks_deep_role_outlier(self):
        output_outlier = calibrate_proven_level(
            league_performance_score=75,
            raw_proven_score=90,
            market_validation_score=40,
            position_group="DM",
        )
        market_verified_player = calibrate_proven_level(
            league_performance_score=74,
            raw_proven_score=68,
            market_validation_score=95,
            position_group="DM",
        )

        self.assertGreater(
            market_verified_player,
            output_outlier,
        )

    def test_comparison_requires_at_least_two_players(self):
        with self.assertRaises(ValueError):
            compare_players(
                "Barcelona",
                [44],
            )

    def test_player_search_returns_empty_result_cleanly(self):
        result = search_players(
            "definitely-not-a-real-player-xyz"
        )

        self.assertEqual(result["count"], 0)
        self.assertEqual(result["players"], [])


if __name__ == "__main__":
    unittest.main()
