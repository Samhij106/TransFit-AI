import unittest

from position_fit_engine import compatibility, get_team_formation_options
from squad_planner_service import (
    STRATEGIES,
    build_squad_plan,
    candidate_plan_fit,
    candidate_role_strength,
    lineup_after_signings,
    optimize_strategy,
    player_starting_selection_score,
)
from league_strength_engine import league_strength_score
from squad_need_engine import squad_role_compatibility


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
        "league_strength": 76,
        "all_competitions": {
            "appearances": 20,
            "starts": 8,
            "minutes": 900,
        },
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

    def test_league_strength_follows_requested_order(self):
        leagues = [
            "Premier League",
            "La Liga",
            "Serie A",
            "Bundesliga",
            "Ligue 1",
        ]
        scores = [league_strength_score(league) for league in leagues]

        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(len(set(scores)), 5)

    def test_wide_midfield_and_wing_roles_are_equivalent(self):
        self.assertEqual(compatibility("LM", "LW"), 100)
        self.assertEqual(compatibility("LW", "LM"), 100)
        self.assertEqual(compatibility("RM", "RW"), 100)
        self.assertEqual(compatibility("RW", "RM"), 100)

        self.assertEqual(
            squad_role_compatibility(
                {
                    "primary_position": "LW",
                    "position_history": "",
                },
                "LM",
            ),
            100,
        )
        self.assertEqual(
            squad_role_compatibility(
                {
                    "primary_position": "RW",
                    "position_history": "",
                },
                "RM",
            ),
            100,
        )

    def test_league_context_places_saka_above_greenwood(self):
        greenwood = candidate(
            70,
            "M. Greenwood",
            55,
            88.8,
            performance=94.4,
            tactical=81.4,
            proven=94.7,
        )
        greenwood["league_strength"] = 82
        saka = candidate(
            71,
            "B. Saka",
            110,
            86,
            performance=87.1,
            tactical=75.4,
            proven=93.7,
        )
        saka["league_strength"] = 100

        self.assertGreater(
            candidate_role_strength(saka),
            candidate_role_strength(greenwood),
        )

    def test_elite_club_rejects_lower_league_bargain_starter(self):
        greenwood = candidate(
            72,
            "M. Greenwood",
            55,
            88.8,
            performance=94.4,
            tactical=81.4,
            proven=94.7,
        )
        greenwood["league_strength"] = 82
        greenwood["deal_feasibility"] = {
            "target_stature_percentile": 97.9,
        }
        assessment = {
            "recruitment_intent": "starter_upgrade",
            "starter_quality": 55,
            "upgrade_baseline": 55,
            "target_incumbent": "A. Semenyo",
        }

        fit = candidate_plan_fit(greenwood, assessment)

        self.assertFalse(fit["eligible"])
        self.assertEqual(
            fit["reason"],
            "Profile is below elite-club starter level",
        )

    def test_manager_trust_keeps_regular_starter_in_lineup(self):
        cubarsi = {
            "appearances": 31,
            "lineups": 31,
            "minutes": 2708,
        }
        rotation_defender = {
            "appearances": 32,
            "lineups": 26,
            "minutes": 2140,
        }

        cubarsi_score = player_starting_selection_score(
            cubarsi, 100, 66.6
        )
        rotation_score = player_starting_selection_score(
            rotation_defender, 100, 74.8
        )

        self.assertGreater(cubarsi_score, rotation_score)

    def test_small_upgrade_margin_does_not_replace_starter(self):
        cherki = candidate(
            50,
            "R. Cherki",
            90,
            88.6,
            performance=88.5,
            tactical=83.4,
            proven=90,
        )
        cherki["league_strength"] = 100
        assessment = {
            "recruitment_intent": "starter_upgrade",
            "starter_quality": 75.7,
            "upgrade_baseline": 88.5,
            "target_incumbent": "Fermín",
        }

        fit = candidate_plan_fit(cherki, assessment)

        self.assertFalse(fit["eligible"])

    def test_depth_signing_does_not_remove_elite_starter(self):
        starting_xi = [{
            "slot_index": 1,
            "role": "RW",
            "player_id": 10,
            "name": "Lamine Yamal",
            "performance_score": 98,
            "is_signing": False,
        }]
        signing = {
            "role": "RW",
            "player_id": 12,
            "name": "Rotation Winger",
            "recruitment_intent": "depth_upgrade",
        }

        lineup = lineup_after_signings(starting_xi, [signing])

        self.assertEqual(lineup[0]["name"], "Lamine Yamal")
        self.assertFalse(lineup[0]["is_signing"])

    def test_transfer_count_is_a_cap_not_a_quota(self):
        roles = [
            {
                "role": "ST",
                "weakness_score": 70,
                "role_strength": 55,
            },
            {
                "role": "CAM",
                "weakness_score": 50,
                "role_strength": 90,
                "starter_quality": 90,
                "upgrade_baseline": 95,
                "recruitment_intent": "starter_upgrade",
            },
        ]
        candidates_by_role = {
            "ST": (candidate(60, "Clear Upgrade", 20, 85),),
            "CAM": (candidate(61, "No Upgrade", 20, 85),),
        }

        plan = optimize_strategy(
            STRATEGIES[1],
            roles,
            candidates_by_role,
            selected_budget=80,
            max_signings=2,
        )

        self.assertIsNotNone(plan)
        self.assertEqual(plan["signing_count"], 1)

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
