from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

import pandas as pd

from candidate_ranking_engine import (
    SUPPORTED_ROLES,
    load_candidate_ranking_data,
    rank_candidates,
)
from position_fit_engine import (
    FORMATION_ROLES,
    apply_selected_formation,
    find_team as find_formation_team,
    get_team_formation_options,
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
from transfer_fit_engine import (
    find_team as find_tactical_team,
    load_data as load_tactical_data,
)
from league_strength_engine import league_strength_score


REFERENCE_RECRUIT_QUALITY = 80
DEFAULT_MAX_SIGNINGS = None
MAX_SIGNINGS = 8
AUTO_MAX_SIGNINGS = 5
ROLE_CANDIDATE_LIMIT = 60
OPTIMIZATION_POOL_SIZE = 10
OPTIMIZATION_BEAM_WIDTH = 2500
AUTO_WEAKNESS_THRESHOLD = 45
STARTER_QUALITY_WEIGHT = 0.78
DEPTH_QUALITY_WEIGHT = 0.22
STARTER_UPGRADE_THRESHOLD = 20
DEPTH_UPGRADE_THRESHOLD = 32
STARTER_UPGRADE_MARGIN = 5
DEPTH_UPGRADE_MARGIN = 5
DEPTH_STARTER_GAP = 6
DEPTH_MAX_MARKET_VALUE = 60
STARTER_SHORTLIST_QUALITY_BAND = 6
ELITE_CLUB_PERCENTILE = 95
ELITE_STARTER_MIN_VALUE_M_EUR = 75
ELITE_STARTER_MIN_LEAGUE_STRENGTH = 90

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


def player_starting_selection_score(player, role_fit, performance):
    """Blend playing level with evidence of the manager's actual XI."""
    appearances = float(player.get("appearances", 0) or 0)
    starts = float(player.get("lineups", 0) or 0)
    minutes = float(player.get("minutes", 0) or 0)
    start_share = (
        min(starts / appearances, 1) * 100
        if appearances > 0
        else 0
    )
    minutes_evidence = min(minutes / 2700, 1) * 100
    manager_trust = (
        start_share * 0.65
        + minutes_evidence * 0.35
    )
    role_adjusted_quality = (
        float(performance) * 0.62
        + manager_trust * 0.38
    )
    return role_adjusted_quality * float(role_fit) / 100


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

            selection_score = player_starting_selection_score(
                player,
                fit,
                performance,
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
    role_context_need=0,
    target_league_strength=90,
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

    starter_quality = float(result["starter_quality"])
    depth_quality = float(result["depth_quality"])
    starter_need = float(result["starter_need"])
    depth_quality_need = float(result["depth_quality_need"])
    coverage_need = float(result["depth_need"])
    role_strength = (
        starter_quality * STARTER_QUALITY_WEIGHT
        + depth_quality * DEPTH_QUALITY_WEIGHT
    )
    weakness_score = clamp(
        starter_need * 0.72
        + depth_quality_need * 0.18
        + coverage_need * 0.10
        + float(role_context_need) * 0.65
    )

    if (
        starter_need >= STARTER_UPGRADE_THRESHOLD
        or role_context_need >= 10
    ):
        recruitment_intent = "starter_upgrade"
    elif (
        depth_quality_need >= DEPTH_UPGRADE_THRESHOLD
        or coverage_need >= 35
    ):
        recruitment_intent = "depth_upgrade"
    else:
        recruitment_intent = "no_action"

    if role_context_need >= 10:
        priority_reason = "Chance conversion can improve"
    elif recruitment_intent == "starter_upgrade":
        priority_reason = "Starting quality can improve"
    elif coverage_need >= 55:
        priority_reason = "Critical depth shortage"
    elif recruitment_intent == "depth_upgrade":
        priority_reason = "Rotation quality can improve"
    else:
        priority_reason = "No material upgrade need"

    starters = result["starters"]
    depth_options = result["depth_options"]
    upgrade_baseline = min(
        (
            float(player["role_quality"]) * 0.70
            + float(target_league_strength) * 0.10
            + 20
            for player in starters
            if player.get("role_quality") is not None
        ),
        default=starter_quality,
    )

    return {
        "role": role,
        "expected_slots": float(result["expected_slots"]),
        "weakness_score": round(weakness_score, 1),
        "depth_need": coverage_need,
        "quality_need": float(result["quality_need"]),
        "incumbent_quality": float(result["incumbent_quality"]),
        "role_strength": round(clamp(role_strength), 1),
        "starter_quality": round(starter_quality, 1),
        "depth_quality": round(depth_quality, 1),
        "starter_need": round(starter_need, 1),
        "depth_quality_need": round(depth_quality_need, 1),
        "role_context_need": round(float(role_context_need), 1),
        "recruitment_intent": recruitment_intent,
        "upgrade_baseline": round(upgrade_baseline, 1),
        "protected_starter": (
            " / ".join(player["name"] for player in starters)
            if starters
            else None
        ),
        "target_incumbent": (
            min(
                starters,
                key=lambda player: player.get(
                    "role_quality", 100
                ),
            )["name"]
            if starters and recruitment_intent == "starter_upgrade"
            else (
                depth_options[-1]["name"]
                if depth_options
                else None
            )
        ),
        "priority_reason": priority_reason,
        "starters": starters,
        "depth_options": depth_options,
        "incumbents": result["incumbents"][:4],
    }


def contextual_role_need(tactical_team, role):
    """Use team style to expose a real finishing gap at striker."""
    if role != "ST" or tactical_team is None:
        return 0

    chance_creation = float(tactical_team.get("chance_creation", 0) or 0)
    attacking_pressure = float(
        tactical_team.get("attacking_pressure", 0) or 0
    )
    shooting_efficiency = float(
        tactical_team.get("shooting_efficiency", 0) or 0
    )
    creation_level = (chance_creation + attacking_pressure) / 2
    return round(clamp(creation_level - shooting_efficiency), 1)


@lru_cache(maxsize=384)
def cached_role_candidates(team_name, role, formation):
    try:
        rankings, _, _ = rank_candidates(
            team_name,
            role,
            ROLE_CANDIDATE_LIMIT,
            min_minutes=450,
            min_role_fit=80,
            budget_millions=None,
            formation=formation,
        )
    except SystemExit:
        return tuple()

    return tuple(rankings.to_dict(orient="records"))


def candidate_summary(candidate, role, assessment=None, plan_fit=None):
    assessment = assessment or {}
    plan_fit = plan_fit or {}
    league_score = candidate.get("league_strength")

    if league_score is None or pd.isna(league_score):
        league_score = league_strength_score(candidate.get("league"))

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
        "league_strength": optional_number(league_score),
        "availability": optional_number(
            candidate["availability"]
        ),
        "potential": optional_number(candidate["potential"]),
        "squad_need": optional_number(candidate["squad_need"]),
        "deal_feasibility": candidate.get("deal_feasibility"),
        "deal_feasibility_score": optional_number(
            candidate.get("deal_feasibility_score")
        ),
        "all_competitions": candidate.get("all_competitions"),
        "recruitment_intent": assessment.get(
            "recruitment_intent", "starter_upgrade"
        ),
        "target_incumbent": plan_fit.get(
            "target_incumbent",
            assessment.get("target_incumbent"),
        ),
        "protected_starter": assessment.get("protected_starter"),
        "projected_role_strength": optional_number(
            plan_fit.get("projected_strength")
        ),
        "upgrade_margin": optional_number(
            plan_fit.get("improvement")
        ),
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
        "performance": competition_adjusted_performance(candidate),
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


def competition_adjusted_performance(candidate):
    """Scale output so weaker competitions cannot inflate recruitment level."""
    league_score = candidate.get("league_strength")

    if league_score is None or pd.isna(league_score):
        league_score = league_strength_score(candidate.get("league"))

    performance = float(candidate["performance"])
    competition_factor = 0.50 + float(league_score) / 200
    return clamp(performance * competition_factor)


def candidate_plan_fit(candidate, assessment):
    intent = assessment.get(
        "recruitment_intent", "starter_upgrade"
    )
    projected_strength = candidate_role_strength(candidate)
    starter_quality = float(
        assessment.get(
            "starter_quality",
            assessment.get("role_strength", 50),
        )
    )
    depth_quality = float(
        assessment.get(
            "depth_quality",
            max(starter_quality - 20, 0),
        )
    )

    if intent == "no_action":
        return {
            "eligible": False,
            "reason": "No material role need",
        }

    if intent == "starter_upgrade":
        baseline = float(
            assessment.get("upgrade_baseline", starter_quality)
        )
        improvement = projected_strength - baseline
        league_score = candidate.get("league_strength")

        if league_score is None or pd.isna(league_score):
            league_score = league_strength_score(candidate.get("league"))

        value = float(candidate.get("estimated_value_m_eur", 0) or 0)
        feasibility = candidate.get("deal_feasibility") or {}
        target_stature = float(
            feasibility.get("target_stature_percentile", 0) or 0
        )
        undersized_elite_profile = (
            target_stature >= ELITE_CLUB_PERCENTILE
            and float(league_score) < ELITE_STARTER_MIN_LEAGUE_STRENGTH
            and value < ELITE_STARTER_MIN_VALUE_M_EUR
        )
        eligible = (
            improvement >= STARTER_UPGRADE_MARGIN
            and not undersized_elite_profile
        )
        return {
            "eligible": eligible,
            "reason": (
                "Clear starter upgrade"
                if eligible
                else (
                    "Profile is below elite-club starter level"
                    if undersized_elite_profile
                    else "Not a clear upgrade on the current starter"
                )
            ),
            "projected_strength": projected_strength,
            "improvement": max(0.0, improvement),
            "target_incumbent": assessment.get("target_incumbent"),
        }

    value = float(candidate.get("estimated_value_m_eur", 0) or 0)
    all_competitions = candidate.get("all_competitions") or {}
    appearances = float(all_competitions.get("appearances", 0) or 0)
    starts = float(all_competitions.get("starts", 0) or 0)
    start_share = starts / appearances if appearances > 0 else 0
    established_starter = starts >= 18 and start_share >= 0.65
    improvement = projected_strength - depth_quality
    below_starter_ceiling = (
        projected_strength <= starter_quality - DEPTH_STARTER_GAP
    )
    affordable_rotation_profile = value <= DEPTH_MAX_MARKET_VALUE
    eligible = (
        improvement >= DEPTH_UPGRADE_MARGIN
        and below_starter_ceiling
        and affordable_rotation_profile
        and not established_starter
    )
    return {
        "eligible": eligible,
        "reason": (
            "Realistic rotation upgrade"
            if eligible
            else "Player profile is too senior for a reserve role"
        ),
        "projected_strength": projected_strength,
        "improvement": max(0.0, improvement),
        "target_incumbent": assessment.get("target_incumbent"),
    }


def optimize_strategy(
    strategy,
    priority_roles,
    candidates_by_role,
    selected_budget,
    max_signings=None,
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
    assessment_by_role = {
        role["role"]: role
        for role in priority_roles
    }

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

            plan_fit = candidate_plan_fit(candidate, role)

            if not plan_fit["eligible"]:
                continue

            utility = candidate_utility(
                candidate,
                role["weakness_score"],
                budget_cap,
                strategy,
            )
            ranked_options.append((utility, candidate, plan_fit))

        ranked_options.sort(
            key=lambda option: option[0],
            reverse=True,
        )

        if (
            role.get("recruitment_intent") == "starter_upgrade"
            and ranked_options
        ):
            best_projected_strength = max(
                option[2]["projected_strength"]
                for option in ranked_options
            )
            ranked_options = [
                option
                for option in ranked_options
                if option[2]["projected_strength"]
                >= best_projected_strength
                - STARTER_SHORTLIST_QUALITY_BAND
            ]

        option_groups.append((
            role_name,
            ranked_options[:OPTIMIZATION_POOL_SIZE],
        ))

    requested_count = (
        None if max_signings is None
        else min(int(max_signings), len(priority_roles))
    )
    states = [{
        "selected": [],
        "player_ids": frozenset(),
        "cost": 0.0,
        "objective": 0.0,
    }]

    for role_name, ranked_options in option_groups:
        assessment = assessment_by_role[role_name]
        expanded = list(states)

        for state in states:
            if (
                requested_count is not None
                and len(state["selected"]) >= requested_count
            ):
                continue

            for utility, candidate, plan_fit in ranked_options:
                player_id = int(candidate["player_id"])
                value = float(candidate["estimated_value_m_eur"])

                if player_id in state["player_ids"]:
                    continue

                if state["cost"] + value > budget_cap + 1e-9:
                    continue

                improvement = float(plan_fit["improvement"])
                depth_impact = float(
                    assessment.get("depth_need", 0)
                ) * 0.08
                impact = improvement + depth_impact
                incremental = (
                    float(utility)
                    + assessment["weakness_score"] * 0.08
                    + impact * 1.15
                )

                if max_signings is None:
                    incremental -= 76

                    if incremental <= 0:
                        continue

                expanded.append({
                    "selected": state["selected"] + [(
                        role_name,
                        utility,
                        candidate,
                        impact,
                        plan_fit,
                    )],
                    "player_ids": state["player_ids"] | {player_id},
                    "cost": state["cost"] + value,
                    "objective": state["objective"] + incremental,
                })

        expanded.sort(
            key=lambda state: (
                state["objective"],
                len(state["selected"]),
                -state["cost"],
            ),
            reverse=True,
        )
        states = expanded[:OPTIMIZATION_BEAM_WIDTH]

    viable_states = [
        state for state in states if state["selected"]
    ]

    best_state = max(
        viable_states,
        key=lambda state: state["objective"],
        default=None,
    )
    best_combo = (
        None if best_state is None
        else best_state["selected"]
    )

    if best_combo is None:
        return None

    signings = [
        candidate_summary(
            candidate,
            role,
            assessment_by_role[role],
            plan_fit,
        )
        for role, _, candidate, _, plan_fit in best_combo
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
    total_impact = sum(
        impact for _, _, _, impact, _ in best_combo
    )
    coverage_target = (
        requested_count
        if requested_count is not None
        else max(1, len(priority_roles))
    )
    coverage_score = len(signings) / coverage_target * 100
    impact_score = clamp(total_impact * 2.5)
    window_score = (
        average_fit * 0.44
        + average_need * 0.16
        + coverage_score * 0.14
        + impact_score * 0.16
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
        "planning_mode": (
            "automatic" if max_signings is None else "capped"
        ),
        "requested_signings": max_signings,
        "upgrade_impact_score": round(impact_score, 1),
    }


def candidate_role_strength(signing):
    league_score = signing.get("league_strength")

    if league_score is None or pd.isna(league_score):
        league_score = league_strength_score(signing.get("league"))

    return clamp(
        competition_adjusted_performance(signing) * 0.47
        + signing["tactical"] * 0.23
        + signing["proven"] * 0.20
        + float(league_score) * 0.10
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
        if signing.get("recruitment_intent") == "depth_upgrade":
            continue

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
    formation=None,
):
    selected_budget = float(budget_millions)

    if selected_budget <= 0:
        raise ValueError("Budget must be greater than zero.")

    if max_signings in (None, ""):
        max_signings = None
    else:
        max_signings = int(max_signings)

        if not 1 <= max_signings <= MAX_SIGNINGS:
            raise ValueError(
                f"Number of transfers must be between 1 and {MAX_SIGNINGS}."
            )
    positions, formation_teams = load_position_data()
    formation_team = find_formation_team(
        formation_teams,
        team_name,
    )
    original_primary_formation = formation_team[
        "primary_formation"
    ]
    formation_team = apply_selected_formation(
        formation_team,
        formation=formation,
        limit=2,
    )
    formation_options = formation_team["formation_options"]
    selected_formation = formation_team["selected_formation"]
    _, tactical_teams = load_tactical_data()
    tactical_team = find_tactical_team(
        tactical_teams,
        formation_team["team"],
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
    formation = selected_formation
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
            contextual_role_need(tactical_team, role),
            league_strength_score(formation_team["league"]),
        )

        if assessment is not None:
            role_assessments.append(assessment)

    role_assessments.sort(
        key=lambda assessment: assessment["weakness_score"],
        reverse=True,
    )
    actionable_assessments = [
        assessment
        for assessment in role_assessments
        if assessment["recruitment_intent"] != "no_action"
    ]

    if max_signings is None:
        priority_roles = [
            assessment
            for assessment in actionable_assessments
            if (
                assessment["weakness_score"] >= AUTO_WEAKNESS_THRESHOLD
                or assessment["depth_need"] >= 45
                or assessment["starter_need"] >= STARTER_UPGRADE_THRESHOLD
                or assessment["depth_quality_need"] >= DEPTH_UPGRADE_THRESHOLD
                or assessment["role_context_need"] >= 10
            )
        ][:AUTO_MAX_SIGNINGS]

        if not priority_roles:
            priority_roles = actionable_assessments[:1]
    else:
        priority_roles = actionable_assessments[:max_signings]

    if not priority_roles:
        raise ValueError(
            "No material squad upgrade need was found for this formation."
        )

    # Warm shared ranking inputs before the role workers start. On the
    # free Render instance this avoids loading every CSV once per role.
    load_candidate_ranking_data()

    with ThreadPoolExecutor(
        max_workers=len(priority_roles)
    ) as executor:
        candidate_groups = list(executor.map(
            lambda assessment: (
                assessment["role"],
                cached_role_candidates(
                    formation_team["team"],
                    assessment["role"],
                    formation,
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
    assessment_by_role = {
        assessment["role"]: assessment
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
            projected_strength = candidate_role_strength(signing)
            assessment = assessment_by_role[role]

            if signing["recruitment_intent"] == "depth_upgrade":
                strengths_after[role] = (
                    assessment["starter_quality"]
                    * STARTER_QUALITY_WEIGHT
                    + max(
                        assessment["depth_quality"],
                        projected_strength,
                    )
                    * DEPTH_QUALITY_WEIGHT
                )
            else:
                strengths_after[role] = max(
                    strengths_after.get(role, 0),
                    projected_strength,
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
            "primary_formation": original_primary_formation,
            "selected_formation": formation,
            "formation_options": formation_options,
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
        "transfer_plan": {
            "mode": (
                "automatic" if max_signings is None else "capped"
            ),
            "requested_signings": max_signings,
            "maximum_supported_signings": MAX_SIGNINGS,
        },
        "reference_recruit_quality": REFERENCE_RECRUIT_QUALITY,
        "starting_xi": starting_xi,
        "team_fit_before": team_fit_before,
        "role_assessments": role_assessments,
        "priority_roles": priority_roles,
        "recommended_strategy": recommended_plan["id"],
        "plans": plans,
        "disclaimer": (
            "Transfer-fee simulation with club-stature and league-level "
            "feasibility. "
            "Wages, contract terms and club willingness to sell are "
            "not modelled."
        ),
    }
