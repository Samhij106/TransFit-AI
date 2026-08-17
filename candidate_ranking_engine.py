import argparse

import pandas as pd

from transfer_fit_engine import (
    load_data as load_tactical_data,
    find_team as find_tactical_team,
    calculate_tactical_fit,
)

from position_fit_engine import (
    load_data as load_position_data,
    find_team as find_formation_team,
)

from age_potential_engine import (
    prepare_data as prepare_potential_data,
    calculate_potential,
)

from squad_need_engine import (
    load_data as load_squad_data,
    prepare_performance_data,
    build_team_squad,
    candidate_role_compatibility,
    calculate_role_demands,
    analyze_role,
)

from transfer_fit_v5 import (
    TACTICAL_WEIGHT,
    POSITION_WEIGHT,
    PERFORMANCE_WEIGHT,
    POTENTIAL_WEIGHT,
    SQUAD_NEED_WEIGHT,
    transfer_fit_label,
)


# =========================================================
# SETTINGS
# =========================================================

SUPPORTED_ROLES = [
    "CB",
    "LB",
    "RB",
    "LWB",
    "RWB",
    "CDM",
    "CM",
    "CAM",
    "LM",
    "RM",
    "LW",
    "RW",
    "ST",
]

DEFAULT_ROLE_COMPATIBILITY = 70


# =========================================================
# FIND RECORD BY PLAYER ID
# =========================================================

def find_by_id(
    dataframe,
    player_id,
):
    result = dataframe[
        dataframe["player_id"]
        == player_id
    ]

    if len(result) != 1:
        return None

    return result.iloc[0]


# =========================================================
# CALCULATE ONE CANDIDATE
# =========================================================

def calculate_candidate_score(
    tactical_player,
    tactical_team,
    position_player,
    formation_team,
    performance_player,
    potential_player,
    squad,
    requested_role,
    expected_slots,
):
    # -----------------------------------------------------
    # Requested role compatibility
    # -----------------------------------------------------

    role_fit = (
        candidate_role_compatibility(
            position_player,
            requested_role,
        )
    )

    # -----------------------------------------------------
    # Tactical Fit
    # -----------------------------------------------------

    tactical_score, _ = (
        calculate_tactical_fit(
            tactical_player,
            tactical_team,
        )
    )

    # -----------------------------------------------------
    # Performance
    # -----------------------------------------------------

    performance_score = float(
        performance_player[
            "performance_score"
        ]
    )

    # -----------------------------------------------------
    # Potential
    # -----------------------------------------------------

    potential_result = (
        calculate_potential(
            potential_player
        )
    )

    potential_score = (
        potential_result[
            "potential_score"
        ]
    )

    # -----------------------------------------------------
    # Role-specific Squad Need
    # -----------------------------------------------------

    squad_result = analyze_role(
        position_player,
        performance_score,
        squad,
        requested_role,
        expected_slots,
        int(
            formation_team[
                "matches_analyzed"
            ]
        ),
    )

    if squad_result is None:
        return None

    squad_need = float(
        squad_result[
            "squad_need"
        ]
    )

    # -----------------------------------------------------
    # Ranking Score
    #
    # IMPORTANT:
    # For candidate ranking we use requested-role fit
    # instead of the player's general Position Fit.
    # -----------------------------------------------------

    final_score = (
        tactical_score
        * TACTICAL_WEIGHT

        + role_fit
        * POSITION_WEIGHT

        + performance_score
        * PERFORMANCE_WEIGHT

        + potential_score
        * POTENTIAL_WEIGHT

        + squad_need
        * SQUAD_NEED_WEIGHT
    )

    # -----------------------------------------------------
    # Photo
    # -----------------------------------------------------

    photo = performance_player.get(
        "photo"
    )

    if pd.isna(photo):
        photo = None

    # -----------------------------------------------------
    # Secondary position
    # -----------------------------------------------------

    secondary_position = (
        position_player[
            "secondary_position"
        ]
    )

    if pd.isna(
        secondary_position
    ):
        secondary_position = "-"

    # -----------------------------------------------------
    # Result
    # -----------------------------------------------------

    return {
        "player_id": int(
            tactical_player[
                "player_id"
            ]
        ),

        "name": tactical_player[
            "name"
        ],

        "photo": photo,

        "current_team": tactical_player[
            "team"
        ],

        "age": potential_result[
            "age"
        ],

        "primary_position": (
            position_player[
                "primary_position"
            ]
        ),

        "secondary_position": (
            secondary_position
        ),

        "minutes": int(
            float(
                performance_player[
                    "minutes"
                ]
            )
        ),

        "role_fit": round(
            role_fit,
            1,
        ),

        "tactical": round(
            tactical_score,
            1,
        ),

        "performance": round(
            performance_score,
            1,
        ),

        "potential": round(
            potential_score,
            1,
        ),

        "squad_need": round(
            squad_need,
            1,
        ),

        "final_score": round(
            final_score,
            1,
        ),

        "classification": (
            transfer_fit_label(
                final_score
            )
        ),
    }


# =========================================================
# RANK CANDIDATES
# =========================================================

def rank_candidates(
    team_name,
    requested_role,
    limit,
    min_minutes,
    min_role_fit,
):
    # -----------------------------------------------------
    # Position / Formation Data
    # -----------------------------------------------------

    (
        positions,
        formation_teams,
    ) = load_position_data()

    formation_team = (
        find_formation_team(
            formation_teams,
            team_name,
        )
    )

    # -----------------------------------------------------
    # Tactical Data
    # -----------------------------------------------------

    (
        tactical_players,
        tactical_teams,
    ) = load_tactical_data()

    tactical_team = (
        find_tactical_team(
            tactical_teams,
            team_name,
        )
    )

    # -----------------------------------------------------
    # Performance Data
    # -----------------------------------------------------

    performance_players = (
        prepare_performance_data()
    )

    # -----------------------------------------------------
    # Potential Data
    # -----------------------------------------------------

    potential_players = (
        prepare_potential_data()
    )

    # -----------------------------------------------------
    # Raw Squad Data
    # -----------------------------------------------------

    (
        raw,
        _,
        _,
    ) = load_squad_data()

    # -----------------------------------------------------
    # Players who played for target team
    #
    # They should not appear as transfer candidates.
    # -----------------------------------------------------

    target_player_ids = set(
        raw[
            raw["team"]
            == formation_team["team"]
        ][
            "player_id"
        ].tolist()
    )

    # -----------------------------------------------------
    # Build target squad once
    # -----------------------------------------------------

    squad = build_team_squad(
        raw,
        positions,
        performance_players,
        formation_team[
            "team"
        ],
        candidate_id=-1,
    )

    # -----------------------------------------------------
    # Requested role demand
    # -----------------------------------------------------

    role_demands = (
        calculate_role_demands(
            formation_team
        )
    )

    expected_slots = (
        role_demands.get(
            requested_role,
            0,
        )
    )

    if expected_slots <= 0:
        raise SystemExit(
            f"\n{formation_team['team']} "
            f"did not use the role "
            f"{requested_role} in the "
            f"2025 formation data."
        )

    # -----------------------------------------------------
    # Candidate Pool
    # -----------------------------------------------------

    results = []

    for _, performance_player in (
        performance_players.iterrows()
    ):
        player_id = int(
            performance_player[
                "player_id"
            ]
        )

        # ---------------------------------------------
        # Skip current/season target-team players
        # ---------------------------------------------

        if (
            player_id
            in target_player_ids
        ):
            continue

        # ---------------------------------------------
        # Goalkeepers not supported
        # ---------------------------------------------

        if (
            performance_player[
                "position_group"
            ]
            == "GK"
        ):
            continue

        # ---------------------------------------------
        # Minutes filter
        # ---------------------------------------------

        minutes = float(
            performance_player[
                "minutes"
            ]
        )

        if minutes < min_minutes:
            continue

        # ---------------------------------------------
        # Get player records by ID
        # ---------------------------------------------

        position_player = (
            find_by_id(
                positions,
                player_id,
            )
        )

        tactical_player = (
            find_by_id(
                tactical_players,
                player_id,
            )
        )

        potential_player = (
            find_by_id(
                potential_players,
                player_id,
            )
        )

        if (
            position_player is None
            or tactical_player is None
            or potential_player is None
        ):
            continue

        # ---------------------------------------------
        # Requested role compatibility filter
        # ---------------------------------------------

        role_fit = (
            candidate_role_compatibility(
                position_player,
                requested_role,
            )
        )

        if role_fit < min_role_fit:
            continue

        # ---------------------------------------------
        # Calculate candidate score
        # ---------------------------------------------

        try:
            result = (
                calculate_candidate_score(
                    tactical_player,
                    tactical_team,
                    position_player,
                    formation_team,
                    performance_player,
                    potential_player,
                    squad,
                    requested_role,
                    expected_slots,
                )
            )

        except SystemExit:
            continue

        if result is not None:
            results.append(
                result
            )

    # -----------------------------------------------------
    # No Candidates
    # -----------------------------------------------------

    if not results:
        raise SystemExit(
            "\nNo suitable candidates found."
        )

    # -----------------------------------------------------
    # DataFrame
    # -----------------------------------------------------

    rankings = pd.DataFrame(
        results
    )

    # -----------------------------------------------------
    # Sort
    # -----------------------------------------------------

    rankings = rankings.sort_values(
        [
            "final_score",
            "role_fit",
        ],
        ascending=[
            False,
            False,
        ],
    ).reset_index(
        drop=True
    )

    # -----------------------------------------------------
    # Rank
    # -----------------------------------------------------

    rankings[
        "rank"
    ] = (
        rankings.index
        + 1
    )

    # -----------------------------------------------------
    # Final column order
    #
    # Photo is included for API / Frontend.
    # -----------------------------------------------------

    rankings = rankings[
        [
            "rank",
            "player_id",
            "name",
            "photo",
            "current_team",
            "age",
            "primary_position",
            "secondary_position",
            "minutes",
            "role_fit",
            "tactical",
            "performance",
            "potential",
            "squad_need",
            "final_score",
            "classification",
        ]
    ]

    return (
        rankings.head(
            limit
        ),
        formation_team,
        expected_slots,
    )


# =========================================================
# DISPLAY
# =========================================================

def print_rankings(
    rankings,
    team,
    requested_role,
    expected_slots,
    min_minutes,
):
    print(
        "\n"
        + "=" * 120
    )

    print(
        "TRANSFIT AI - CANDIDATE RANKING ENGINE"
    )

    print(
        "=" * 120
    )

    print(
        f"\nTarget Team:     "
        f"{team['team']}"
    )

    print(
        f"Target Role:     "
        f"{requested_role}"
    )

    print(
        f"Main Formation:  "
        f"{team['primary_formation']}"
    )

    print(
        f"Expected Slots:  "
        f"{round(expected_slots, 2)}"
    )

    print(
        f"Minimum Minutes: "
        f"{min_minutes}"
    )

    print(
        "\nTarget-team players from the "
        "2025 season are excluded."
    )

    print(
        "\n"
        + "-" * 120
    )

    # -----------------------------------------------------
    # Hide photo + player_id from terminal table
    #
    # They remain available in API response.
    # -----------------------------------------------------

    display = rankings.drop(
        columns=[
            "photo",
            "player_id",
        ],
        errors="ignore",
    ).copy()

    display = display.rename(
        columns={
            "rank": "#",

            "name": "Player",

            "current_team": (
                "Current Team"
            ),

            "age": "Age",

            "primary_position": (
                "Primary"
            ),

            "secondary_position": (
                "Secondary"
            ),

            "minutes": "Minutes",

            "role_fit": (
                "Role Fit"
            ),

            "tactical": (
                "Tactical"
            ),

            "performance": (
                "Performance"
            ),

            "potential": (
                "Potential"
            ),

            "squad_need": (
                "Squad Need"
            ),

            "final_score": (
                "Ranking Score"
            ),

            "classification": (
                "Classification"
            ),
        }
    )

    print(
        "\n"
        + display.to_string(
            index=False
        )
    )

    print(
        "\n"
        + "=" * 120
    )


# =========================================================
# MAIN
# =========================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "TransFit AI "
            "Candidate Ranking Engine"
        )
    )

    parser.add_argument(
        "team",
        help="Target team",
    )

    parser.add_argument(
        "role",
        help=(
            "Target role, for example "
            "RW, ST, CM, CB"
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help=(
            "Number of candidates to show"
        ),
    )

    parser.add_argument(
        "--min-minutes",
        type=int,
        default=450,
        help=(
            "Minimum season minutes required"
        ),
    )

    parser.add_argument(
        "--min-role-fit",
        type=float,
        default=(
            DEFAULT_ROLE_COMPATIBILITY
        ),
        help=(
            "Minimum compatibility "
            "with target role"
        ),
    )

    args = parser.parse_args()

    requested_role = (
        args.role
        .strip()
        .upper()
    )

    # -----------------------------------------------------
    # Validate Role
    # -----------------------------------------------------

    if (
        requested_role
        not in SUPPORTED_ROLES
    ):
        raise SystemExit(
            "\nUnsupported role. "
            f"Choose one of:\n"
            f"{', '.join(SUPPORTED_ROLES)}"
        )

    # -----------------------------------------------------
    # Rank
    # -----------------------------------------------------

    (
        rankings,
        team,
        expected_slots,
    ) = rank_candidates(
        args.team,
        requested_role,
        args.limit,
        args.min_minutes,
        args.min_role_fit,
    )

    # -----------------------------------------------------
    # Display
    # -----------------------------------------------------

    print_rankings(
        rankings,
        team,
        requested_role,
        expected_slots,
        args.min_minutes,
    )


if __name__ == "__main__":
    main()