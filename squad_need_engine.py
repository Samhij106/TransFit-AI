import argparse
import math
from collections import Counter

import pandas as pd

from position_fit_engine import (
    FORMATION_ROLES,
    compatibility,
    parse_position_history,
    parse_formation_history,
)

from performance_fit_engine import (
    load_data as load_performance_data,
    calculate_percentiles,
    calculate_performance_score,
)


# =========================================================
# FILES
# =========================================================

RAW_FILE = "data/raw/big_five_players_2025.csv"
POSITION_FILE = (
    "data/processed/"
    "player_positions_big_five_2025.csv"
)
FORMATION_FILE = "data/processed/team_formation_profiles_2025.csv"


# =========================================================
# SETTINGS
# =========================================================

# Extra coverage beyond exact starting minutes
DEPTH_BUFFER = 1.25

# Adjacent positions count less toward true squad depth
ADJACENT_DEPTH_DISCOUNT = 0.55


# =========================================================
# HELPERS
# =========================================================

def clamp(value, low=0, high=100):
    return max(
        low,
        min(high, value)
    )


def finite_number(value, default=0.0):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float(default)

    if not math.isfinite(number):
        return float(default)

    return number


# =========================================================
# LOAD DATA
# =========================================================

def load_data():
    raw = pd.read_csv(
        RAW_FILE
    )

    positions = pd.read_csv(
        POSITION_FILE
    )

    formations = pd.read_csv(
        FORMATION_FILE
    )

    return (
        raw,
        positions,
        formations,
    )


# =========================================================
# FIND TEAM
# =========================================================

def find_team(
    formations,
    team_name,
):
    query = (
        team_name
        .strip()
        .lower()
    )

    exact = formations[
        formations["team"]
        .astype(str)
        .str.lower()
        == query
    ]

    if len(exact) == 1:
        return exact.iloc[0]

    partial = formations[
        formations["team"]
        .astype(str)
        .str.lower()
        .str.contains(
            query,
            regex=False,
        )
    ]

    if len(partial) == 1:
        return partial.iloc[0]

    if len(partial) > 1:
        print(
            "\nMultiple teams found:\n"
        )

        print(
            partial["team"]
            .to_string(index=False)
        )

        raise SystemExit(
            "\nPlease enter a more specific team name."
        )

    raise SystemExit(
        f"\nTeam not found: {team_name}"
    )


# =========================================================
# PREPARE PERFORMANCE DATA
# =========================================================

def prepare_performance_data():
    players = (
        load_performance_data()
    )

    players = (
        calculate_percentiles(
            players
        )
    )

    scores = []

    for _, player in players.iterrows():

        # GK performance engine not supported yet
        if (
            player["position_group"]
            == "GK"
        ):
            scores.append(
                None
            )

            continue

        try:
            result = (
                calculate_performance_score(
                    player
                )
            )

            scores.append(
                result[
                    "performance_score"
                ]
            )

        except SystemExit:
            scores.append(
                None
            )

    players[
        "performance_score"
    ] = scores

    return players


# =========================================================
# RESOLVE PLAYER
#
# Finds player using names from BOTH datasets.
# Then all later joins use player_id.
# =========================================================

def resolve_candidate(
    performance,
    positions,
    player_name=None,
    player_id=None,
):
    if player_id is not None:
        player_id = int(player_id)

    elif player_name:
        query = (
            player_name
            .strip()
            .lower()
        )

        # -------------------------------------------------
        # Exact match in performance dataset
        # -------------------------------------------------

        perf_exact = performance[
            performance["name"]
            .astype(str)
            .str.lower()
            == query
        ]

        if len(perf_exact) == 1:

            player_id = int(
                perf_exact.iloc[0][
                    "player_id"
                ]
            )

        else:

            # ---------------------------------------------
            # Exact match in position dataset
            # ---------------------------------------------

            position_exact = positions[
                positions["name"]
                .astype(str)
                .str.lower()
                == query
            ]

            if len(position_exact) == 1:

                player_id = int(
                    position_exact.iloc[0][
                        "player_id"
                    ]
                )

            else:

                # -----------------------------------------
                # Partial search in both datasets
                # -----------------------------------------

                perf_partial = performance[
                    performance["name"]
                    .astype(str)
                    .str.lower()
                    .str.contains(
                        query,
                        regex=False,
                    )
                ]

                position_partial = positions[
                    positions["name"]
                    .astype(str)
                    .str.lower()
                    .str.contains(
                        query,
                        regex=False,
                    )
                ]

                ids = (
                    set(
                        perf_partial[
                            "player_id"
                        ].tolist()
                    )
                    |
                    set(
                        position_partial[
                            "player_id"
                        ].tolist()
                    )
                )

                if len(ids) == 1:

                    player_id = int(
                        next(
                            iter(ids)
                        )
                    )

                elif len(ids) > 1:

                    print(
                        "\nMultiple players found:\n"
                    )

                    combined = pd.concat(
                        [
                            perf_partial[
                                [
                                    "player_id",
                                    "name",
                                ]
                            ],
                            position_partial[
                                [
                                    "player_id",
                                    "name",
                                ]
                            ],
                        ]
                    )

                    combined = (
                        combined
                        .drop_duplicates()
                        .sort_values(
                            "player_id"
                        )
                    )

                    print(
                        combined.to_string(
                            index=False
                        )
                    )

                    raise SystemExit(
                        "\nPlease enter a more specific player name."
                    )

                else:

                    raise SystemExit(
                        f"\nPlayer not found: "
                        f"{player_name}"
                    )

    else:
        raise ValueError(
            "player_name or player_id is required."
        )

    # -----------------------------------------------------
    # Get records by ID
    # -----------------------------------------------------

    performance_player = performance[
        performance["player_id"]
        == player_id
    ]

    position_player = positions[
        positions["player_id"]
        == player_id
    ]

    if (
        len(performance_player)
        != 1
    ):
        raise SystemExit(
            f"\nPerformance data not found "
            f"for player_id {player_id}"
        )

    if (
        len(position_player)
        != 1
    ):
        raise SystemExit(
            f"\nPosition data not found "
            f"for player_id {player_id}"
        )

    return (
        performance_player.iloc[0],
        position_player.iloc[0],
    )


# =========================================================
# FORMATION ROLE DEMAND
# =========================================================

def calculate_role_demands(
    team,
):
    history = (
        parse_formation_history(
            team[
                "formation_history"
            ]
        )
    )

    if not history:
        raise SystemExit(
            "\nNo formation history available."
        )

    total_matches = sum(
        history.values()
    )

    role_slots = {}

    for (
        formation,
        matches,
    ) in history.items():

        roles = FORMATION_ROLES.get(
            formation
        )

        if not roles:
            continue

        usage = (
            matches
            / total_matches
        )

        counts = Counter(
            roles
        )

        for (
            role,
            count,
        ) in counts.items():

            role_slots[
                role
            ] = (
                role_slots.get(
                    role,
                    0
                )
                + usage * count
            )

    return role_slots


# =========================================================
# CANDIDATE ROLE COMPATIBILITY
# =========================================================

def candidate_role_compatibility(
    player,
    role,
):
    history = (
        parse_position_history(
            player.get(
                "position_history"
            )
        )
    )

    # -----------------------------------------------------
    # Use actual position history
    # -----------------------------------------------------

    if history:

        total_starts = sum(
            history.values()
        )

        weighted_score = 0

        for (
            position,
            starts,
        ) in history.items():

            score = compatibility(
                position,
                role,
            )

            weighted_score += (
                score
                * starts
            )

        if total_starts > 0:

            return (
                weighted_score
                / total_starts
            )

    # -----------------------------------------------------
    # Fallback
    # -----------------------------------------------------

    primary = player.get(
        "primary_position"
    )

    secondary = player.get(
        "secondary_position"
    )

    primary_score = (
        compatibility(
            primary,
            role,
        )
    )

    secondary_score = 0

    if not pd.isna(
        secondary
    ):
        secondary_score = (
            compatibility(
                secondary,
                role,
            )
        )

    return max(
        primary_score,
        secondary_score * 0.85,
    )


# =========================================================
# SQUAD DEPTH COMPATIBILITY
#
# Natural positions count fully.
# Adjacent roles are discounted.
# =========================================================

def squad_role_compatibility(
    player,
    role,
):
    history = (
        parse_position_history(
            player.get(
                "position_history"
            )
        )
    )

    if history:

        total_starts = sum(
            history.values()
        )

        weighted_score = 0

        for (
            position,
            starts,
        ) in history.items():

            natural_compatibility = compatibility(
                position,
                role,
            )

            if natural_compatibility == 100:

                score = 100

            else:

                score = (
                    natural_compatibility
                    * ADJACENT_DEPTH_DISCOUNT
                )

            weighted_score += (
                score
                * starts
            )

        if total_starts > 0:

            return (
                weighted_score
                / total_starts
            )

    primary = player.get(
        "primary_position"
    )

    if pd.isna(
        primary
    ):
        return 0

    natural_compatibility = compatibility(
        primary,
        role,
    )

    if natural_compatibility == 100:
        return 100

    return (
        natural_compatibility
        * ADJACENT_DEPTH_DISCOUNT
    )


# =========================================================
# BUILD TEAM SEASON SQUAD
# =========================================================

def build_team_squad(
    raw,
    positions,
    performance,
    team_name,
    candidate_id,
):
    squad = raw[
        raw["team"]
        == team_name
    ].copy()

    # -----------------------------------------------------
    # Position data
    # -----------------------------------------------------

    position_columns = positions[
        [
            "player_id",
            "primary_position",
            "secondary_position",
            "position_history",
        ]
    ]

    squad = squad.merge(
        position_columns,
        on="player_id",
        how="left",
    )

    # -----------------------------------------------------
    # Performance data
    # -----------------------------------------------------

    performance_columns = performance[
        [
            "player_id",
            "performance_score",
        ]
    ]

    squad = squad.merge(
        performance_columns,
        on="player_id",
        how="left",
    )

    # -----------------------------------------------------
    # Remove candidate if he already played
    # for target team during this season.
    # -----------------------------------------------------

    squad = squad[
        squad["player_id"]
        != candidate_id
    ].copy()

    squad[
        "minutes"
    ] = pd.to_numeric(
        squad["minutes"],
        errors="coerce",
    ).fillna(0)

    return squad


# =========================================================
# ANALYZE ONE ROLE
# =========================================================

def analyze_role(
    candidate,
    candidate_performance,
    squad,
    role,
    expected_slots,
    matches_analyzed,
):
    candidate_compat = (
        candidate_role_compatibility(
            candidate,
            role,
        )
    )

    # Ignore clearly unrealistic roles
    if candidate_compat < 40:
        return None

    # =====================================================
    # FORMATION DEMAND
    # =====================================================

    demand_score = clamp(
        expected_slots * 100
    )

    # =====================================================
    # REQUIRED MINUTES
    # =====================================================

    required_minutes = (
        expected_slots
        * matches_analyzed
        * 90
        * DEPTH_BUFFER
    )

    incumbents = []

    total_effective_minutes = 0

    # =====================================================
    # EXISTING SQUAD COVERAGE
    # =====================================================

    for _, player in squad.iterrows():

        depth_compat = (
            squad_role_compatibility(
                player,
                role,
            )
        )

        if depth_compat <= 0:
            continue

        minutes = finite_number(player.get("minutes"))
        appearances = finite_number(player.get("appearances"))
        lineups = finite_number(player.get("lineups"))

        effective_minutes = (
            minutes
            * depth_compat
            / 100
        )

        total_effective_minutes += (
            effective_minutes
        )

        performance_score = player[
            "performance_score"
        ]

        if pd.isna(
            performance_score
        ):
            role_quality = None

        else:
            role_quality = (
                float(
                    performance_score
                )
                * depth_compat
                / 100
            )

        start_share = (
            min(lineups / appearances, 1) * 100
            if appearances > 0
            else 0
        )
        minutes_evidence = min(
            minutes
            / max(matches_analyzed * 90, 1)
            * 100,
            100,
        )
        squad_status = (
            start_share * 0.65
            + minutes_evidence * 0.35
        )
        status_role_score = (
            squad_status
            * depth_compat
            / 100
        )
        squad_role_quality = (
            None
            if role_quality is None
            else role_quality * 0.55
            + status_role_score * 0.45
        )

        incumbents.append(
            {
                "name": player[
                    "name"
                ],

                "minutes": round(
                    minutes
                ),

                "role_compatibility": round(
                    depth_compat,
                    1,
                ),

                "effective_minutes": round(
                    effective_minutes
                ),

                "starts": round(lineups),

                "start_share": round(
                    start_share,
                    1,
                ),

                "squad_status": round(
                    squad_status,
                    1,
                ),

                "performance_score": (
                    None
                    if pd.isna(
                        performance_score
                    )
                    else round(
                        float(
                            performance_score
                        ),
                        1,
                    )
                ),

                "role_quality": (
                    None
                    if role_quality is None
                    else round(
                        role_quality,
                        1,
                    )
                ),

                "squad_role_quality": (
                    None
                    if squad_role_quality is None
                    else round(
                        squad_role_quality,
                        1,
                    )
                ),
            }
        )

    # =====================================================
    # DEPTH NEED
    # =====================================================

    if required_minutes > 0:

        coverage_ratio = (
            total_effective_minutes
            / required_minutes
        )

    else:

        coverage_ratio = 1

    depth_need = clamp(
        (
            1
            - coverage_ratio
        )
        * 100
    )

    # =====================================================
    # INCUMBENT QUALITY
    # =====================================================

    incumbents = sorted(
        incumbents,
        key=lambda player: (
            player.get("squad_role_quality")
            if player.get("squad_role_quality") is not None
            else -1
        ),
        reverse=True,
    )

    starter_count = max(
        1,
        math.ceil(expected_slots),
    )
    starter_options = [
        player
        for player in incumbents[:starter_count]
        if player.get("squad_role_quality") is not None
    ]
    depth_options = [
        player
        for player in incumbents[
            starter_count:starter_count * 2
        ]
        if player.get("squad_role_quality") is not None
    ]

    starter_quality = (
        sum(
            player["squad_role_quality"]
            for player in starter_options
        ) / len(starter_options)
        if starter_options
        else 50
    )
    depth_quality = (
        sum(
            player["squad_role_quality"]
            for player in depth_options
        ) / len(depth_options)
        if depth_options
        else 0
    )

    # The regular starter(s) define most of the role's quality.
    # Depth remains relevant, but cannot make an elite starter look
    # like a weak position simply because the reserve is developing.
    incumbent_quality = (
        starter_quality * 0.75
        + depth_quality * 0.25
    )

    # =====================================================
    # QUALITY NEED
    #
    # Low incumbent quality =
    # high need for quality improvement.
    # =====================================================

    quality_need = clamp(
        100
        - incumbent_quality
    )
    starter_need = clamp(100 - starter_quality)
    depth_quality_need = clamp(100 - depth_quality)

    # =====================================================
    # CANDIDATE ROLE QUALITY
    # =====================================================

    candidate_role_quality = (
        candidate_performance
        * candidate_compat
        / 100
    )

    # =====================================================
    # UPGRADE OPPORTUNITY
    #
    # 50 = approximately same level
    # >50 = candidate improves role
    # <50 = candidate weaker
    # =====================================================

    upgrade_opportunity = clamp(
        50
        + (
            candidate_role_quality
            - incumbent_quality
        )
        * 1.25
    )

    # =====================================================
    # BASE SQUAD NEED
    #
    # Depth             35%
    # Quality Need      30%
    # Upgrade           25%
    # Formation Demand  10%
    # =====================================================

    base_need = (
        depth_need * 0.35
        + quality_need * 0.30
        + upgrade_opportunity * 0.25
        + demand_score * 0.10
    )

    # =====================================================
    # MODIFIERS
    # =====================================================

    # Rarely used tactical roles should
    # contribute less.
    demand_modifier = (
        0.65
        + 0.35
        * demand_score
        / 100
    )

    # Candidate must actually be capable
    # of playing this role.
    compatibility_modifier = (
        0.60
        + 0.40
        * candidate_compat
        / 100
    )

    squad_need = (
        base_need
        * demand_modifier
        * compatibility_modifier
    )

    squad_need = clamp(
        squad_need
    )

    # =====================================================
    # SORT INCUMBENTS
    # =====================================================

    incumbents = sorted(
        incumbents,
        key=lambda x: (
            x.get("squad_role_quality")
            if x.get("squad_role_quality") is not None
            else -1
        ),
        reverse=True,
    )

    # =====================================================
    # RESULT
    # =====================================================

    return {
        "role": role,

        "expected_slots": round(
            expected_slots,
            2,
        ),

        "formation_demand": round(
            demand_score,
            1,
        ),

        "candidate_compatibility": round(
            candidate_compat,
            1,
        ),

        "required_minutes": round(
            required_minutes
        ),

        "effective_squad_minutes": round(
            total_effective_minutes
        ),

        "depth_need": round(
            depth_need,
            1,
        ),

        "quality_need": round(
            quality_need,
            1,
        ),

        "incumbent_quality": round(
            incumbent_quality,
            1,
        ),

        "starter_count": starter_count,

        "starter_quality": round(
            starter_quality,
            1,
        ),

        "depth_quality": round(
            depth_quality,
            1,
        ),

        "starter_need": round(
            starter_need,
            1,
        ),

        "depth_quality_need": round(
            depth_quality_need,
            1,
        ),

        "starters": starter_options,

        "depth_options": depth_options,

        "candidate_role_quality": round(
            candidate_role_quality,
            1,
        ),

        "upgrade_opportunity": round(
            upgrade_opportunity,
            1,
        ),

        "squad_need": round(
            squad_need,
            1,
        ),

        "incumbents": incumbents,
    }


# =========================================================
# CALCULATE SQUAD NEED
# =========================================================

def calculate_squad_need(
    candidate,
    candidate_performance,
    team,
    squad,
):
    role_demands = (
        calculate_role_demands(
            team
        )
    )

    matches_analyzed = int(
        team[
            "matches_analyzed"
        ]
    )

    role_results = []

    for (
        role,
        expected_slots,
    ) in role_demands.items():

        if role == "GK":
            continue

        result = analyze_role(
            candidate,
            candidate_performance,
            squad,
            role,
            expected_slots,
            matches_analyzed,
        )

        if result is not None:

            role_results.append(
                result
            )

    if not role_results:

        raise SystemExit(
            "\nNo compatible squad role "
            "found for this player."
        )

    role_results = sorted(
        role_results,
        key=lambda x: x[
            "squad_need"
        ],
        reverse=True,
    )

    best = role_results[0]

    return (
        best,
        role_results,
    )


# =========================================================
# LABEL
# =========================================================

def squad_need_label(
    score,
):
    if score >= 75:
        return "High Squad Need"

    if score >= 60:
        return "Meaningful Squad Need"

    if score >= 45:
        return "Moderate Squad Need"

    if score >= 30:
        return "Low Squad Need"

    return "Very Low Squad Need"


# =========================================================
# DISPLAY
# =========================================================

def print_result(
    candidate,
    team,
    best,
    role_results,
):
    print(
        "\n"
        + "=" * 88
    )

    print(
        "TRANSFIT AI - SEASON SQUAD NEED ANALYSIS"
    )

    print(
        "=" * 88
    )

    print(
        f"\nPlayer:       "
        f"{candidate['name']}"
    )

    print(
        f"Target Team:  "
        f"{team['team']}"
    )

    print(
        f"Primary Formation: "
        f"{team['primary_formation']}"
    )

    print(
        "\nScope: 2025 season squad usage "
        "(not a live roster snapshot)"
    )

    print(
        "\n"
        + "-" * 88
    )

    print(
        f"\nSQUAD NEED SCORE: "
        f"{best['squad_need']} / 100"
    )

    print(
        f"Classification: "
        f"{squad_need_label(best['squad_need'])}"
    )

    print(
        f"Best Squad Role: "
        f"{best['role']}"
    )

    print(
        "\n"
        + "-" * 88
    )

    print(
        "\nSCORE BREAKDOWN\n"
    )

    print(
        f"Formation Demand:     "
        f"{best['formation_demand']} / 100"
    )

    print(
        f"Depth Need:           "
        f"{best['depth_need']} / 100"
    )

    print(
        f"Quality Need:         "
        f"{best['quality_need']} / 100"
    )

    print(
        f"Upgrade Opportunity:  "
        f"{best['upgrade_opportunity']} / 100"
    )

    print(
        f"Candidate Role Fit:   "
        f"{best['candidate_compatibility']} / 100"
    )

    print(
        f"\nExpected Role Slots:  "
        f"{best['expected_slots']}"
    )

    print(
        f"Required Minutes:     "
        f"{best['required_minutes']}"
    )

    print(
        f"Effective Squad Min:  "
        f"{best['effective_squad_minutes']}"
    )

    print(
        f"\nIncumbent Quality:    "
        f"{best['incumbent_quality']} / 100"
    )

    print(
        f"Candidate Role Quality: "
        f"{best['candidate_role_quality']} / 100"
    )

    print(
        "\n"
        + "-" * 88
    )

    print(
        "\nTOP ROLE OPTIONS\n"
    )

    role_table = pd.DataFrame(
        [
            {
                "Role": r[
                    "role"
                ],

                "Candidate Fit": r[
                    "candidate_compatibility"
                ],

                "Demand": r[
                    "formation_demand"
                ],

                "Depth Need": r[
                    "depth_need"
                ],

                "Quality Need": r[
                    "quality_need"
                ],

                "Upgrade": r[
                    "upgrade_opportunity"
                ],

                "Squad Need": r[
                    "squad_need"
                ],
            }
            for r in role_results[
                :5
            ]
        ]
    )

    print(
        role_table.to_string(
            index=False
        )
    )

    print(
        "\n"
        + "-" * 88
    )

    print(
        f"\nTOP INCUMBENTS "
        f"FOR {best['role']}\n"
    )

    incumbent_table = (
        pd.DataFrame(
            best[
                "incumbents"
            ][
                :5
            ]
        )
    )

    if incumbent_table.empty:

        print(
            "No meaningful incumbent "
            "depth found."
        )

    else:

        print(
            incumbent_table.to_string(
                index=False
            )
        )

    print(
        "\n"
        + "=" * 88
    )


# =========================================================
# MAIN
# =========================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "TransFit AI "
            "Season Squad Need Engine"
        )
    )

    parser.add_argument(
        "player",
        help="Player name",
    )

    parser.add_argument(
        "team",
        help="Target team",
    )

    args = parser.parse_args()

    # -----------------------------------------------------
    # Load
    # -----------------------------------------------------

    (
        raw,
        positions,
        formations,
    ) = load_data()

    performance = (
        prepare_performance_data()
    )

    # -----------------------------------------------------
    # Resolve player
    # -----------------------------------------------------

    (
        candidate_perf,
        candidate_position,
    ) = resolve_candidate(
        performance,
        positions,
        args.player,
    )

    candidate_id = int(
        candidate_perf[
            "player_id"
        ]
    )

    # -----------------------------------------------------
    # GK check
    # -----------------------------------------------------

    if (
        candidate_perf[
            "position_group"
        ]
        == "GK"
    ):

        raise SystemExit(
            "\nGoalkeeper squad need "
            "analysis is not supported yet."
        )

    # -----------------------------------------------------
    # Team
    # -----------------------------------------------------

    team = find_team(
        formations,
        args.team,
    )

    # -----------------------------------------------------
    # Build season squad
    # -----------------------------------------------------

    squad = build_team_squad(
        raw,
        positions,
        performance,
        team[
            "team"
        ],
        candidate_id,
    )

    # -----------------------------------------------------
    # Candidate performance
    # -----------------------------------------------------

    performance_result = (
        calculate_performance_score(
            candidate_perf
        )
    )

    candidate_performance = (
        performance_result[
            "performance_score"
        ]
    )

    # -----------------------------------------------------
    # Calculate Squad Need
    # -----------------------------------------------------

    (
        best,
        role_results,
    ) = calculate_squad_need(
        candidate_position,
        candidate_performance,
        team,
        squad,
    )

    # -----------------------------------------------------
    # Use canonical full player name
    # -----------------------------------------------------

    candidate_position = (
        candidate_position.copy()
    )

    candidate_position[
        "name"
    ] = candidate_perf[
        "name"
    ]

    # -----------------------------------------------------
    # Display
    # -----------------------------------------------------

    print_result(
        candidate_position,
        team,
        best,
        role_results,
    )


if __name__ == "__main__":
    main()
