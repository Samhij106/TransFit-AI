import argparse

import pandas as pd

from transfer_fit_engine import (
    load_data as load_tactical_data,
    find_team as find_tactical_team,
    calculate_tactical_fit,
)

from position_fit_engine import (
    FORMATION_ROLES,
    apply_selected_formation,
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
    PROVEN_WEIGHT,
    AVAILABILITY_WEIGHT,
    POTENTIAL_WEIGHT,
    SQUAD_NEED_WEIGHT,
    DEAL_FEASIBILITY_WEIGHT,
    LEAGUE_STRENGTH_WEIGHT,
    SCORE_VERSION,
    SCORE_WEIGHTS,
    transfer_fit_label,
)

from realistic_data_engine import (
    blend_performance_score,
    calibrate_proven_level,
    find_realism_by_id,
    load_realism_profiles,
    realism_scores,
)

from transfer_value_engine import (
    assess_budget,
    resolve_transfer_value,
)
from league_strength_engine import league_strength_score
from transfer_realism_engine import assess_transfer_feasibility


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

DEFAULT_ROLE_COMPATIBILITY = 80

# Candidate eligibility is based on the canonical
# Transfermarkt profile position, not temporary formation
# slots from match lineups. Closely related flank roles are
# grouped because Transfermarkt profiles generally use
# full-back rather than wing-back as the canonical label.
NATURAL_ROLE_POSITIONS = {
    "CB": {"CB"},
    "LB": {"LB", "LWB"},
    "LWB": {"LB", "LWB"},
    "RB": {"RB", "RWB"},
    "RWB": {"RB", "RWB"},
    "CDM": {"CDM"},
    "CM": {"CM"},
    "CAM": {"CAM"},
    "LM": {"LM", "LW"},
    "LW": {"LW", "LM"},
    "RM": {"RM", "RW"},
    "RW": {"RW", "RM"},
    "ST": {"ST"},
}


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


def is_natural_role_candidate(
    position_player,
    requested_role,
):
    primary_position = str(
        position_player.get(
            "primary_position",
            "",
        )
    ).strip().upper()
    allowed_positions = (
        NATURAL_ROLE_POSITIONS.get(
            requested_role,
            set(),
        )
    )

    return primary_position in allowed_positions


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
    realism_player=None,
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

    league_performance_score = float(
        performance_player[
            "performance_score"
        ]
    )

    realism = realism_scores(
        realism_player,
        league_performance_score,
        performance_player["minutes"],
    )
    performance_score = blend_performance_score(
        league_performance_score,
        realism["production_score"],
        performance_player["position_group"],
    )
    proven_score = calibrate_proven_level(
        league_performance_score,
        realism["raw_proven_score"],
        realism["market_validation_score"],
        performance_player["position_group"],
    )
    availability_score = realism[
        "availability_score"
    ]
    league_score = league_strength_score(
        performance_player.get("league")
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

    transfer_value = resolve_transfer_value(
        player_id=int(
            tactical_player["player_id"]
        ),
        performance_score=performance_score,
        potential_score=potential_score,
        age=potential_result["age"],
        minutes=performance_player["minutes"],
        league=performance_player.get("league"),
        position_group=performance_player[
            "position_group"
        ],
        position_source=position_player.get(
            "position_source"
        ),
    )

    transfer_feasibility = assess_transfer_feasibility(
        target_team=formation_team["team"],
        current_team=tactical_player["team"],
        player_value_m_eur=transfer_value[
            "estimated_value_m_eur"
        ],
        performance_score=performance_score,
        proven_score=proven_score,
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

        + proven_score
        * PROVEN_WEIGHT

        + availability_score
        * AVAILABILITY_WEIGHT

        + potential_score
        * POTENTIAL_WEIGHT

        + squad_need
        * SQUAD_NEED_WEIGHT

        + transfer_feasibility["score"]
        * DEAL_FEASIBILITY_WEIGHT

        + league_score
        * LEAGUE_STRENGTH_WEIGHT
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

        "league": performance_player.get(
            "league"
        ),

        "position_source": position_player.get(
            "position_source",
            None,
        ),

        "estimated_value_m_eur": (
            transfer_value[
                "estimated_value_m_eur"
            ]
        ),

        "value_confidence": transfer_value[
            "confidence"
        ],

        "value_model": transfer_value[
            "model"
        ],

        "value_source": transfer_value[
            "value_source"
        ],

        "value_source_label": transfer_value[
            "value_source_label"
        ],

        "value_source_url": transfer_value[
            "value_source_url"
        ],

        "value_updated_at": transfer_value[
            "value_updated_at"
        ],

        "transfermarkt_player_id": transfer_value[
            "transfermarkt_player_id"
        ],

        "value_match_method": transfer_value[
            "value_match_method"
        ],

        "is_model_estimate": transfer_value[
            "is_model_estimate"
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

        "league_performance": round(
            league_performance_score,
            1,
        ),

        "production": round(
            realism["production_score"],
            1,
        ),

        "proven": round(
            proven_score,
            1,
        ),

        "raw_proven": round(
            realism["raw_proven_score"],
            1,
        ),

        "market_validation": (
            None
            if realism["market_validation_score"] is None
            else round(
                realism["market_validation_score"],
                1,
            )
        ),

        "score_contributions": {
            "tactical": round(
                tactical_score * TACTICAL_WEIGHT,
                2,
            ),
            "role": round(
                role_fit * POSITION_WEIGHT,
                2,
            ),
            "performance": round(
                performance_score * PERFORMANCE_WEIGHT,
                2,
            ),
            "proven": round(
                proven_score * PROVEN_WEIGHT,
                2,
            ),
            "availability": round(
                availability_score * AVAILABILITY_WEIGHT,
                2,
            ),
            "potential": round(
                potential_score * POTENTIAL_WEIGHT,
                2,
            ),
            "squad_need": round(
                squad_need * SQUAD_NEED_WEIGHT,
                2,
            ),
            "deal_feasibility": round(
                transfer_feasibility["score"]
                * DEAL_FEASIBILITY_WEIGHT,
                2,
            ),
            "league_strength": round(
                league_score * LEAGUE_STRENGTH_WEIGHT,
                2,
            ),
        },

        "availability": round(
            availability_score,
            1,
        ),

        "all_competitions": {
            "appearances": realism[
                "current_appearances"
            ],
            "starts": realism[
                "current_starts"
            ],
            "minutes": realism[
                "current_minutes"
            ],
            "goals": realism[
                "current_goals"
            ],
            "assists": realism[
                "current_assists"
            ],
            "source": realism[
                "data_source"
            ],
        },

        "potential": round(
            potential_score,
            1,
        ),

        "squad_need": round(
            squad_need,
            1,
        ),

        "deal_feasibility": transfer_feasibility,

        "deal_feasibility_score": transfer_feasibility[
            "score"
        ],

        "league_strength": round(
            league_score,
            1,
        ),

        "transfer_realistic": transfer_feasibility[
            "eligible"
        ],

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
    budget_millions=None,
    formation=None,
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

    formation_team = apply_selected_formation(
        formation_team,
        formation=formation,
        limit=2,
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

    realism_players = (
        load_realism_profiles()
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

        realism_player = find_realism_by_id(
            realism_players,
            player_id,
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

        if not is_natural_role_candidate(
            position_player,
            requested_role,
        ):
            continue

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
                    realism_player,
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

    rankings = rankings[
        rankings["transfer_realistic"]
    ].copy()

    if rankings.empty:
        raise SystemExit(
            "\nNo candidates passed the club-stature and "
            "transfer-realism checks."
        )

    # -----------------------------------------------------
    # Budget filter
    #
    # Sporting fit remains unchanged. Budget only controls
    # eligibility and labels candidates within the allowed
    # 15% stretch range.
    # -----------------------------------------------------

    if budget_millions is not None:
        budget_assessments = rankings[
            "estimated_value_m_eur"
        ].apply(
            lambda value: assess_budget(
                value,
                budget_millions,
            )
        )

        rankings["budget_status"] = (
            budget_assessments.apply(
                lambda value: value[
                    "budget_status"
                ]
            )
        )
        rankings[
            "budget_difference_m_eur"
        ] = budget_assessments.apply(
            lambda value: value[
                "budget_difference_m_eur"
            ]
        )

        rankings = rankings[
            rankings["budget_status"]
            != "over_budget"
        ].copy()

        if rankings.empty:
            raise SystemExit(
                "\nNo suitable candidates found "
                "within the selected budget and "
                "15% tolerance."
            )

    else:
        rankings["budget_status"] = (
            "not_set"
        )
        rankings[
            "budget_difference_m_eur"
        ] = None

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
            "league",
            "age",
            "primary_position",
            "secondary_position",
            "position_source",
            "estimated_value_m_eur",
            "value_confidence",
            "value_model",
            "value_source",
            "value_source_label",
            "value_source_url",
            "value_updated_at",
            "transfermarkt_player_id",
            "value_match_method",
            "is_model_estimate",
            "budget_status",
            "budget_difference_m_eur",
            "minutes",
            "role_fit",
            "tactical",
            "performance",
            "league_performance",
            "production",
            "proven",
            "raw_proven",
            "market_validation",
            "score_contributions",
            "availability",
            "all_competitions",
            "potential",
            "squad_need",
            "deal_feasibility",
            "deal_feasibility_score",
            "league_strength",
            "transfer_realistic",
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
