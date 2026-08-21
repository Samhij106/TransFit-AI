import unittest

from position_fit_engine import get_team_formation_options
from squad_planner_service import (
    STRATEGIES,
    build_squad_plan,
    candidate_role_strength,
    lineup_after_signings,
    optimize_strategy,
)


def candidate(
    player_id,
    name,
    value,
    final_score,
    performance=80,
    tactical=80,
    proven=80,
):
    return {
        "player_id": player_id,
        "name": name,
        "photo": None,
        "current_team": "Test Club",
        "league": "Test League",
        "age": 25,
        "primary_position": "ST",
        "estimated_value_m_eur": value,
        "value_source_label": "Transfermarkt",
        "is_model_estimate": False,
        "final_score": final_score,
        "role_fit": 100,
        "tactical": tactical,
        "performance": performance,
        "proven": proven,
        "availability": 90,
        "potential": 75,
        "squad_need": 70,
    }


class SquadPlannerTests(unittest.TestCase):
    def test_top_two_verified_formations_preserve_usage(self):
        team = {
            "primary_formation": "4-2-3-1",
            "formation_history": (
                "4-2-3-1:20 | 3-4-2-1:10 | "
                "4-3-3:5 | 4-4-2:3"
            ),
        }

        options = get_team_formation_options(team, limit=2)

        self.assertEqual(
            [option["formation"] for option in options],
            ["4-2-3-1", "3-4-2-1"],
        )
        self.assertEqual(options[0]["matches"], 20)
        self.assertEqual(options[0]["usage_percentage"], 52.6)
        self.assertTrue(options[0]["is_primary"])

    def test_budget_must_be_positive(self):
        with self.assertRaises(ValueError):
            build_squad_plan("Barcelona", 0)

    def test_safe_plan_never_exceeds_selected_budget(self):
        priority_roles = [
            {
                "role": "ST",
                "weakness_score": 70,
            },
            {
                "role": "CB",
                "weakness_score": 60,
            },
        ]
        candidates_by_role = {
            "ST": (
                candidate(1, "Striker A", 55, 88),
                candidate(2, "Striker B", 30, 80),
            ),
            "CB": (
                candidate(3, "Defender A", 40, 86),
                candidate(4, "Defender B", 20, 78),
            ),
        }

        plan = optimize_strategy(
            STRATEGIES[0],
            priority_roles,
            candidates_by_role,
            selected_budget=60,
            max_signings=2,
        )

        self.assertIsNotNone(plan)
        self.assertLessEqual(plan["total_cost_m_eur"], 60)
        self.assertEqual(plan["budget_status"], "within_budget")
        self.assertEqual(
            len({item["player_id"] for item in plan["signings"]}),
            plan["signing_count"],
        )

    def test_signing_replaces_weakest_player_in_matching_role(self):
        starting_xi = [
            {
                "slot_index": 1,
                "role": "CB",
                "player_id": 10,
                "name": "First Centre Back",
                "performance_score": 78,
                "is_signing": False,
            },
            {
                "slot_index": 2,
                "role": "CB",
                "player_id": 11,
                "name": "Second Centre Back",
                "performance_score": 66,
                "is_signing": False,
            },
        ]
        signing = {
            "role": "CB",
            "player_id": 12,
            "name": "New Centre Back",
            "photo": None,
            "current_team": "Test Club",
            "age": 24,
            "primary_position": "CB",
            "performance": 84,
        }

        lineup = lineup_after_signings(starting_xi, [signing])
        replacement = next(
            player for player in lineup if player.get("is_signing")
        )

        self.assertEqual(replacement["slot_index"], 2)
        self.assertEqual(replacement["replaces"], "Second Centre Back")

    def test_projected_role_strength_is_bounded(self):
        signing = {
            "performance": 120,
            "tactical": 110,
            "proven": 105,
        }

        self.assertEqual(candidate_role_strength(signing), 100)

    def test_optimizer_supports_more_than_three_transfers(self):
        roles = []
        candidates_by_role = {}

        for index, role in enumerate(["LB", "CB", "CM", "ST"]):
            roles.append({
                "role": role,
                "weakness_score": 70 - index,
                "role_strength": 55,
                "depth_need": 45,
            })
            candidates_by_role[role] = (
                candidate(index + 20, f"Player {role}", 10, 82),
            )

        plan = optimize_strategy(
            STRATEGIES[1],
            roles,
            candidates_by_role,
            selected_budget=50,
            max_signings=4,
        )

        self.assertIsNotNone(plan)
        self.assertEqual(plan["signing_count"], 4)


if __name__ == "__main__":
    unittest.main()
