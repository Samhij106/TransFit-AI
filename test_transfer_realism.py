import unittest

from transfer_realism_engine import assess_transfer_feasibility


class TransferRealismTests(unittest.TestCase):
    def test_superstar_move_to_alaves_is_rejected(self):
        result = assess_transfer_feasibility(
            target_team="Alaves",
            current_team="Manchester City",
            player_value_m_eur=200,
            performance_score=96,
            proven_score=99,
        )

        self.assertFalse(result["eligible"])
        self.assertEqual(result["status"], "unrealistic")
        self.assertLess(result["score"], 35)

    def test_elite_club_can_enter_superstar_market(self):
        result = assess_transfer_feasibility(
            target_team="Barcelona",
            current_team="Manchester City",
            player_value_m_eur=200,
            performance_score=96,
            proven_score=99,
        )

        self.assertTrue(result["eligible"])
        self.assertGreaterEqual(result["score"], 70)


if __name__ == "__main__":
    unittest.main()
