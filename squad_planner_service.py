import itertools
import math
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

import pandas as pd

from candidate_ranking_engine import (
    SUPPORTED_ROLES,
    rank_candidates,
)
from position_fit_engine import (
    FORMATION_ROLES,
    find_team as find_formation_team,
    load_data as load_position_data,
)
from squad_need_engine import (
    analyze_role,
    build_team_squad,
    calculate_role_demands,
    load_data as load_squad_data,
    prepare_performance_data,
    squad_role_compatibility,
)
from transfer_fit_v5 import SCORE_VERSION, SCORE_WEIGHTS
from transfer_value_engine import BUDGET_TOLERANCE


REFERENCE_RECRUIT_QUALITY = 80
DEFAULT_MAX_SIGNINGS = 3
ROLE_CANDIDATE_LIMIT = 60
OPTIMIZATION_POOL_SIZE = 14

STRATEGIES = (
    {
        "id": "safe",
        "name": "Safe Window",
        "label": "PROVEN VALUE",
        "description": (
            "Prioritizes proven level, availability and "
            "responsible use of the available budget."
        ),
        "budget_multiplier": 1.0,
        "target_utilization": 0.78,
        "weights": {
            "final_score": 0.34,
            "proven": 0.23,
            "availability": 0.16,
            "affordability": 0.20,
            "weakness": 0.07,
        },
    },
    {
        "id": "balanced",
        "name": "Balanced Window",
        "label": "FIT + VALUE",
        "description": (
            "Balances immediate sporting fit, proven quality, "
            "potential and total investment."
        ),
        "budget_multiplier": 1.0,
        "target_utilization": 0.92,
        "weights": {
            "final_score": 0.50,
            "proven": 0.13,
            "potential": 0.12,
            "affordability": 0.13,
            "weakness": 0.12,
        },
    },
    {
        "id": "ambitious",
        "name": "Ambitious Window",
        "label": "MAXIMUM UPSIDE",
        "description": (
            "Maximizes sporting quality and upside, using the "
            "existing 15% budget tolerance when justified."
        ),
        "budget_multiplier": 1 + BUDGET_TOLERANCE,
        "target_utilization": 0.98,
        "weights": {
            "final_score": 0.60,
            "performance": 0.14,
            "potential": 0.12,
            "proven": 0.06,
            "weakness": 0.08,
        },
    },
)


def clamp(value, low=0, high=100):
    return max(low, min(high, value))


def optional_number(value, digits=1):
    if value is None or pd.isna(value):
        return None

    return round(float(value), digits)


def optional_text(value):
    if value is None or pd.isna(value):
        return None

    return str(value)


def player_record(player, role, slot_index=None):
    primary_position = player.get("primary_position")

    if pd.isna(primary_position):
        primary_position = (
            "GK"
            if str(player.get("position", "")).lower()
            == "goalkeeper"
            else None
        )

    return {
        "slot_index": slot_index,
        "role": role,
        "player_id": int(player["player_id"]),
        "name": player["name"],
        "photo": optional_text(player.get("photo")),
        "current_team": optional_text(player.get("team")),
        "age": optional_number(player.get("age")),
        "primary_position": primary_position,
        "minutes": optional_number(player.get("minutes"), 0),
        "performance_score": optional_number(
            player.get("performance_score")
        ),
        "is_signing": False,
    }


def starting_xi_for_formation(squad, formation):
    roles = FORMATION_ROLES.get(formation)

    if not roles:
        raise ValueError(f"Unsupported formation: {formation}")

    used_player_ids = set()
    assignments = {}
    slots = list(enumerate(roles))

    def compatible_count(slot):
        _, role = slot

        if role == "GK":
            return int((
                squad["position"]
                .astype(str)
                .str.lower()
                == "goalkeeper"
            ).sum())

        return sum(
            squad_role_compatibility(player, role) > 0
            for _, player in squad.iterrows()
        )

    for slot_index, role in sorted(
        slots,
        key=lambda slot: (
            compatible_count(slot),
            slot[0],
        ),
    ):
        options = []

        for _, player in squad.iterrows():
            player_id = int(player["player_id"])

            if player_id in used_player_ids:
                continue

            if role == "GK":
                is_goalkeeper = (
                    str(player.get("position", "")).lower()
                    == "goalkeeper"
                )

                if not is_goalkeeper:
                    continue

                fit = 100
                performance = 50
            else:
                fit = squad_role_compatibility(player, role)

                if fit <= 0:
                    continue

                performance = player.get("performance_score")
                performance = (
                    50
                    if pd.isna(performance)
                    else float(performance)
                )

            minutes = float(player.get("minutes", 0) or 0)
            availability_bonus = min(minutes / 2700, 1) * 8
            selection_score = (
                performance * fit / 100
                + availability_bonus
            )
            options.append((selection_score, player))

        if not options:
            continue

        _, selected = max(options, key=lambda option: option[0])
        selected_id = int(selected["player_id"])
        used_player_ids.add(selected_id)
        assignments[slot_index] = player_record(
            selected,
            role,
            slot_index,
        )

    return [
        assignments[index]
        for index in range(len(roles))
        if index in assignments
    ]


def role_assessment(
    squad,
    role,
    expected_slots,
    matches_analyzed,
):
    reference_candidate = pd.Series({
        "primary_position": role,
        "secondary_position": None,
        "position_history": None,
    })
    result = analyze_role(
        reference_candidate,
        REFERENCE_RECRUIT_QUALITY,
        squad,
        role,
        expected_slots,
        matches_analyzed,
    )

    if result is None:
        return None

    role_strength = (
        float(result["incumbent_quality"]) * 0.72
        + (100 - float(result["depth_need"])) * 0.28
    )

    if result["depth_need"] >= 55:
        priority_reason = "Critical depth shortage"
    elif result["quality_need"] >= 42:
        priority_reason = "Starting quality can improve"
    elif result["upgrade_opportunity"] >= 65:
        priority_reason = "Strong upgrade opportunity"
    else:
        priority_reason = "Tactical depth opportunity"

    return {
        "role": role,
        "expected_slots": float(result["expected_slots"]),
        "weakness_score": float(result["squad_need"]),
        "depth_need": float(result["depth_need"]),
        "quality_need": float(result["quality_need"]),
        "incumbent_quality": float(result["incumbent_quality"]),
        "role_strength": round(clamp(role_strength), 1),
        "priority_reason": priority_reason,
        "incumbents": result["incumbents"][:3],
    }


@lru_cache(maxsize=256)
def cached_role_candidates(team_name, role):
    rankings, _, _ = rank_candidates(
        team_name,
        role,
        ROLE_CANDIDATE_LIMIT,
        min_minutes=450,
        min_role_fit=80,
        budget_millions=None,
    )

    return tuple(rankings.to_dict(orient="records"))


def candidate_summary(candidate, role):
    return {
        "role": role,
        "player_id": int(candidate["player_id"]),
        "name": candidate["name"],
        "photo": optional_text(candidate.get("photo")),
        "current_team": candidate["current_team"],
        "league": optional_text(candidate.get("league")),
        "age": optional_number(candidate.get("age")),
        "primary_position": candidate["primary_position"],
        "market_value_m_eur": optional_number(
            candidate["estimated_value_m_eur"]
        ),
        "value_source_label": optional_text(
            candidate.get("value_source_label")
        ),
        "is_model_estimate": bool(
            candidate.get("is_model_estimate", False)
        ),
        "transfit_score": optional_number(
            candidate["final_score"]
        ),
        "role_fit": optional_number(candidate["role_fit"]),
        "tactical": optional_number(candidate["tactical"]),
        "performance": optional_number(
            candidate["performance"]
        ),
        "proven": optional_number(candidate["proven"]),
        "availability": optional_number(
            candidate["availability"]
        ),
        "potential": optional_number(candidate["potential"]),
        "squad_need": optional_number(candidate["squad_need"]),
    }


def candidate_utility(
    candidate,
    role_weakness,
    budget_cap,
    strategy,
):
    value = float(candidate["estimated_value_m_eur"])
    affordability = clamp(
        100 - value / max(budget_cap, 1) * 75
    )
    metrics = {
        "final_score": float(candidate["final_score"]),
        "performance": float(candidate["performance"]),
        "proven": float(candidate["proven"]),
        "availability": float(candidate["availability"]),
        "potential": float(candidate["potential"]),
        "affordability": affordability,
        "weakness": float(role_weakness),
    }

    return sum(
        metrics[key] * weight
        for key, weight in strategy["weights"].items()
    )


def optimize_strategy(
    strategy,
    priority_roles,
    candidates_by_role,
    selected_budget,
    max_signings,
):
    budget_cap = round(
        selected_budget * strategy["budget_multiplier"],
        1,
    )
    weakness_by_role = {
        role["role"]: role["weakness_score"]
        for role in priority_roles
    }
    option_groups = []

    for role in priority_roles:
        role_name = role["role"]
        ranked_options = []

        for candidate in candidates_by_role.get(role_name, ()):
            value = candidate.get("estimated_value_m_eur")

            if value is None or pd.isna(value):
                continue

            value = float(value)

            if value <= 0 or value > budget_cap:
                continue

            utility = candidate_utility(
                candidate,
                role["weakness_score"],
                budget_cap,
                strategy,
            )
            ranked_options.append((utility, candidate))

        ranked_options.sort(
            key=lambda option: option[0],
            reverse=True,
        )
        option_groups.append(
            [(None, None)]
            + ranked_options[:OPTIMIZATION_POOL_SIZE]
        )

    best_combo = None
    best_objective = -math.inf

    for combination in itertools.product(*option_groups):
        selected = [
            (priority_roles[index]["role"], utility, candidate)
            for index, (utility, candidate) in enumerate(combination)
            if candidate is not None
        ]

        if not selected or len(selected) > max_signings:
            continue

        player_ids = [
            int(candidate["player_id"])
            for _, _, candidate in selected
        ]

        if len(player_ids) != len(set(player_ids)):
            continue

        total_cost = sum(
            float(candidate["estimated_value_m_eur"])
            for _, _, candidate in selected
        )

        if total_cost > budget_cap + 1e-9:
            continue

        coverage_bonus = len(selected) * 14
        weakness_bonus = sum(
            weakness_by_role[role] * 0.08
            for role, _, _ in selected
        )
        objective = (
            sum(float(utility) for _, utility, _ in selected)
            + coverage_bonus
            + weakness_bonus
        )

        if objective > best_objective:
            best_objective = objective
            best_combo = selected

    if best_combo is None:
        return None

    signings = [
        candidate_summary(candidate, role)
        for role, _, candidate in best_combo
    ]
    total_cost = round(
        sum(signing["market_value_m_eur"] for signing in signings),
        1,
    )
    utilization = total_cost / max(selected_budget, 1)
    target_utilization = strategy["target_utilization"]
    budget_efficiency = clamp(
        100
        - abs(utilization - target_utilization)
        / max(target_utilization, 0.1)
        * 70
    )
    average_fit = sum(
        signing["transfit_score"] for signing in signings
    ) / len(signings)
    average_need = sum(
        weakness_by_role[signing["role"]]
        for signing in signings
    ) / len(signings)
    coverage_score = len(signings) / max_signings * 100
    window_score = (
        average_fit * 0.52
        + average_need * 0.20
        + coverage_score * 0.18
        + budget_efficiency * 0.10
    )

    return {
        "id": strategy["id"],
        "name": strategy["name"],
        "label": strategy["label"],
        "description": strategy["description"],
        "signings": signings,
        "signing_count": len(signings),
        "total_cost_m_eur": total_cost,
        "remaining_budget_m_eur": round(
            selected_budget - total_cost,
            1,
        ),
        "maximum_budget_m_eur": budget_cap,
        "budget_status": (
            "stretch"
            if total_cost > selected_budget
            else "within_budget"
        ),
        "window_score": round(clamp(window_score), 1),
    }


def candidate_role_strength(signing):
    return clamp(
        signing["performance"] * 0.55
        + signing["tactical"] * 0.25
        + signing["proven"] * 0.20
    )


def weighted_team_fit(role_assessments, strengths):
    total_weight = sum(
        assessment["expected_slots"]
        for assessment in role_assessments
    )

    if total_weight <= 0:
        return 0

    return round(
        sum(
            strengths[assessment["role"]]
            * assessment["expected_slots"]
            for assessment in role_assessments
        )
        / total_weight,
        1,
    )


def lineup_after_signings(starting_xi, signings):
    lineup = [dict(player) for player in starting_xi]

    for signing in signings:
        matching_slots = [
            (index, player)
            for index, player in enumerate(lineup)
            if player["role"] == signing["role"]
            and not player.get("is_signing")
        ]

        if not matching_slots:
            continue

        replace_index, replaced = min(
            matching_slots,
            key=lambda item: (
                item[1].get("performance_score")
                if item[1].get("performance_score") is not None
                else -1
            ),
        )
        lineup[replace_index] = {
            "slot_index": replaced["slot_index"],
            "role": signing["role"],
            "player_id": signing["player_id"],
            "name": signing["name"],
            "photo": signing["photo"],
            "current_team": signing["current_team"],
            "age": signing["age"],
            "primary_position": signing["primary_position"],
            "minutes": None,
            "performance_score": signing["performance"],
            "is_signing": True,
            "replaces": replaced["name"],
        }

    return lineup


def build_squad_plan(
    team_name,
    budget_millions,
    max_signings=DEFAULT_MAX_SIGNINGS,
):
    selected_budget = float(budget_millions)

    if selected_budget <= 0:
        raise ValueError("Budget must be greater than zero.")

    max_signings = max(1, min(int(max_signings), 3))
    positions, formation_teams = load_position_data()
    formation_team = find_formation_team(
        formation_teams,
        team_name,
    )
    raw, _, _ = load_squad_data()
    performance_players = prepare_performance_data()
    squad = build_team_squad(
        raw,
        positions,
        performance_players,
        formation_team["team"],
        candidate_id=-1,
    )
    formation = formation_team["primary_formation"]
    formation_roles = FORMATION_ROLES.get(formation)

    if not formation_roles:
        raise ValueError(
            f"Unsupported primary formation: {formation}"
        )

    primary_roles = list(dict.fromkeys(
        role
        for role in formation_roles
        if role != "GK" and role in SUPPORTED_ROLES
    ))
    role_demands = calculate_role_demands(formation_team)
    matches_analyzed = int(formation_team["matches_analyzed"])
    role_assessments = []

    for role in primary_roles:
        expected_slots = float(role_demands.get(role, 0))

        if expected_slots <= 0:
            continue

        assessment = role_assessment(
            squad,
            role,
            expected_slots,
            matches_analyzed,
        )

        if assessment is not None:
            role_assessments.append(assessment)

    role_assessments.sort(
        key=lambda assessment: assessment["weakness_score"],
        reverse=True,
    )
    priority_roles = role_assessments[:max_signings]

    if not priority_roles:
        raise ValueError("No eligible outfield roles found.")

    with ThreadPoolExecutor(
        max_workers=len(priority_roles)
    ) as executor:
        candidate_groups = list(executor.map(
            lambda assessment: (
                assessment["role"],
                cached_role_candidates(
                    formation_team["team"],
                    assessment["role"],
                ),
            ),
            priority_roles,
        ))

    candidates_by_role = dict(candidate_groups)
    plans = []

    for strategy in STRATEGIES:
        plan = optimize_strategy(
            strategy,
            priority_roles,
            candidates_by_role,
            selected_budget,
            max_signings,
        )

        if plan is not None:
            plans.append(plan)

    if not plans:
        raise ValueError(
            "No realistic transfer plan fits the selected budget."
        )

    strengths_before = {
        assessment["role"]: assessment["role_strength"]
        for assessment in role_assessments
    }
    team_fit_before = weighted_team_fit(
        role_assessments,
        strengths_before,
    )
    starting_xi = starting_xi_for_formation(squad, formation)

    for plan in plans:
        strengths_after = dict(strengths_before)

        for signing in plan["signings"]:
            role = signing["role"]
            strengths_after[role] = max(
                strengths_after.get(role, 0),
                candidate_role_strength(signing),
            )

        team_fit_after = weighted_team_fit(
            role_assessments,
            strengths_after,
        )
        plan["team_fit_before"] = team_fit_before
        plan["team_fit_after"] = team_fit_after
        plan["team_fit_improvement"] = round(
            team_fit_after - team_fit_before,
            1,
        )
        plan["after_lineup"] = lineup_after_signings(
            starting_xi,
            plan["signings"],
        )

    recommended_plan = max(
        plans,
        key=lambda plan: plan["window_score"],
    )

    for plan in plans:
        plan["recommended"] = (
            plan["id"] == recommended_plan["id"]
        )

    return {
        "scoring_model": {
            "version": SCORE_VERSION,
            "weights": SCORE_WEIGHTS,
        },
        "team": {
            "team_id": int(formation_team["team_id"]),
            "name": formation_team["team"],
            "league": formation_team["league"],
            "primary_formation": formation,
            "matches_analyzed": matches_analyzed,
        },
        "budget": {
            "selected_m_eur": round(selected_budget, 1),
            "tolerance_percentage": BUDGET_TOLERANCE * 100,
            "maximum_m_eur": round(
                selected_budget * (1 + BUDGET_TOLERANCE),
                1,
            ),
        },
        "reference_recruit_quality": REFERENCE_RECRUIT_QUALITY,
        "starting_xi": starting_xi,
        "team_fit_before": team_fit_before,
        "role_assessments": role_assessments,
        "priority_roles": priority_roles,
        "recommended_strategy": recommended_plan["id"],
        "plans": plans,
        "disclaimer": (
            "Transfer-fee simulation only. Wages, contract terms and "
            "club willingness to sell are not modelled."
        ),
    }
