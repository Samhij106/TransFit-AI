import argparse

from transfer_fit_engine import (
    load_data as load_tactical_data,
    find_team as find_tactical_team,
    calculate_tactical_fit,
)

from position_fit_engine import (
    load_data as load_position_data,
    find_team as find_formation_team,
    calculate_position_fit,
)

from performance_fit_engine import (
    calculate_performance_score,
)

from age_potential_engine import (
    prepare_data as prepare_potential_data,
    calculate_potential,
)

from squad_need_engine import (
    load_data as load_squad_data,
    prepare_performance_data,
    resolve_candidate,
    build_team_squad,
    calculate_squad_need,
    squad_need_label,
)

from realistic_data_engine import (
    blend_performance_score,
    realism_scores,
)


# =========================================================
# TRANSFER FIT V6 WEIGHTS
# =========================================================

TACTICAL_WEIGHT = 0.20
POSITION_WEIGHT = 0.15
PERFORMANCE_WEIGHT = 0.25
PROVEN_WEIGHT = 0.20
AVAILABILITY_WEIGHT = 0.10
POTENTIAL_WEIGHT = 0.05
SQUAD_NEED_WEIGHT = 0.05


# =========================================================
# FIND RECORD BY PLAYER ID
# =========================================================

def find_player_by_id(
    players,
    player_id,
    source_name,
):
    match = players[
        players["player_id"] == player_id
    ]

    if len(match) == 1:
        return match.iloc[0]

    if len(match) > 1:
        raise SystemExit(
            f"\nMultiple {source_name} records "
            f"found for player_id {player_id}"
        )

    raise SystemExit(
        f"\n{source_name} data not found "
        f"for player_id {player_id}"
    )


# =========================================================
# LABEL
# =========================================================

def transfer_fit_label(score):
    if score >= 90:
        return "Elite Transfer Fit"

    if score >= 80:
        return "Strong Transfer Fit"

    if score >= 70:
        return "Good Transfer Fit"

    if score >= 60:
        return "Moderate Transfer Fit"

    return "Low Transfer Fit"


# =========================================================
# CALCULATE TRANSFER FIT V6
# =========================================================

def calculate_transfer_fit_v5(
    tactical_player,
    tactical_team,
    position_player,
    formation_team,
    performance_player,
    potential_player,
    squad,
    realism_player=None,
):
    # -----------------------------------------------------
    # 1. Tactical Fit
    # -----------------------------------------------------

    tactical_score, tactical_details = (
        calculate_tactical_fit(
            tactical_player,
            tactical_team,
        )
    )

    # -----------------------------------------------------
    # 2. Position Fit
    # -----------------------------------------------------

    position_score, position_details = (
        calculate_position_fit(
            position_player,
            formation_team,
        )
    )

    # -----------------------------------------------------
    # 3. Performance
    # -----------------------------------------------------

    performance_result = (
        calculate_performance_score(
            performance_player
        )
    )

    league_performance_score = (
        performance_result[
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
    )
    proven_score = realism[
        "proven_score"
    ]
    availability_score = realism[
        "availability_score"
    ]

    # -----------------------------------------------------
    # 4. Potential
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
    # 5. Squad Need
    # -----------------------------------------------------

    squad_best, squad_role_results = (
        calculate_squad_need(
            position_player,
            performance_score,
            formation_team,
            squad,
        )
    )

    squad_need_score = (
        squad_best[
            "squad_need"
        ]
    )

    # -----------------------------------------------------
    # Contributions
    # -----------------------------------------------------

    tactical_contribution = (
        tactical_score
        * TACTICAL_WEIGHT
    )

    position_contribution = (
        position_score
        * POSITION_WEIGHT
    )

    performance_contribution = (
        performance_score
        * PERFORMANCE_WEIGHT
    )

    proven_contribution = (
        proven_score
        * PROVEN_WEIGHT
    )

    availability_contribution = (
        availability_score
        * AVAILABILITY_WEIGHT
    )

    potential_contribution = (
        potential_score
        * POTENTIAL_WEIGHT
    )

    squad_need_contribution = (
        squad_need_score
        * SQUAD_NEED_WEIGHT
    )

    final_score = (
        tactical_contribution
        + position_contribution
        + performance_contribution
        + proven_contribution
        + availability_contribution
        + potential_contribution
        + squad_need_contribution
    )

    return {
        "final_score": round(
            final_score,
            1,
        ),

        "tactical_score": round(
            tactical_score,
            1,
        ),

        "position_score": round(
            position_score,
            1,
        ),

        "performance_score": round(
            performance_score,
            1,
        ),

        "league_performance_score": round(
            league_performance_score,
            1,
        ),

        "production_score": round(
            realism["production_score"],
            1,
        ),

        "proven_score": round(
            proven_score,
            1,
        ),

        "availability_score": round(
            availability_score,
            1,
        ),

        "realism_details": realism,

        "potential_score": round(
            potential_score,
            1,
        ),

        "squad_need_score": round(
            squad_need_score,
            1,
        ),

        "tactical_contribution": round(
            tactical_contribution,
            2,
        ),

        "position_contribution": round(
            position_contribution,
            2,
        ),

        "performance_contribution": round(
            performance_contribution,
            2,
        ),

        "proven_contribution": round(
            proven_contribution,
            2,
        ),

        "availability_contribution": round(
            availability_contribution,
            2,
        ),

        "potential_contribution": round(
            potential_contribution,
            2,
        ),

        "squad_need_contribution": round(
            squad_need_contribution,
            2,
        ),

        "tactical_details": tactical_details,

        "position_details": position_details,

        "performance_details": (
            performance_result[
                "details"
            ]
        ),

        "performance_reliability": (
            performance_result[
                "reliability"
            ]
        ),

        "potential_result": (
            potential_result
        ),

        "squad_best": squad_best,

        "squad_role_results": (
            squad_role_results
        ),
    }


# =========================================================
# DISPLAY
# =========================================================

def print_result(
    tactical_player,
    tactical_team,
    position_player,
    formation_team,
    result,
):
    print(
        "\n"
        + "=" * 88
    )

    print(
        "TRANSFIT AI - TRANSFER FIT V6"
    )

    print(
        "=" * 88
    )

    print(
        f"\nPlayer:       "
        f"{tactical_player['name']}"
    )

    print(
        f"Current Team: "
        f"{tactical_player['team']}"
    )

    print(
        f"Target Team:  "
        f"{tactical_team['team']}"
    )

    print(
        f"Position:     "
        f"{position_player['primary_position']}"
    )

    secondary = (
        position_player.get(
            "secondary_position"
        )
    )

    if (
        secondary is None
        or str(secondary) == "nan"
    ):
        secondary = "-"

    print(
        f"Secondary:    {secondary}"
    )

    print(
        f"Age:          "
        f"{result['potential_result']['age']}"
    )

    print(
        f"Formation:    "
        f"{formation_team['primary_formation']}"
    )

    print(
        "\nScope: Squad Need is based on "
        "2025 season squad usage."
    )

    print(
        "\n"
        + "-" * 88
    )

    print(
        f"\nFINAL TRANSFER FIT: "
        f"{result['final_score']} / 100"
    )

    print(
        f"Classification: "
        f"{transfer_fit_label(result['final_score'])}"
    )

    print(
        "\n"
        + "-" * 88
    )

    print(
        "\nSCORE BREAKDOWN\n"
    )

    print(
        f"Tactical Fit: "
        f"{result['tactical_score']} / 100 "
        f"x 20% = "
        f"{result['tactical_contribution']}"
    )

    print(
        f"Position Fit: "
        f"{result['position_score']} / 100 "
        f"x 15% = "
        f"{result['position_contribution']}"
    )

    print(
        f"Performance:  "
        f"{result['performance_score']} / 100 "
        f"x 25% = "
        f"{result['performance_contribution']}"
    )

    print(
        f"Proven Level: "
        f"{result['proven_score']} / 100 "
        f"x 20% = "
        f"{result['proven_contribution']}"
    )

    print(
        f"Availability: "
        f"{result['availability_score']} / 100 "
        f"x 10% = "
        f"{result['availability_contribution']}"
    )

    print(
        f"Potential:    "
        f"{result['potential_score']} / 100 "
        f"x 5% = "
        f"{result['potential_contribution']}"
    )

    print(
        f"Squad Need:   "
        f"{result['squad_need_score']} / 100 "
        f"x 5% = "
        f"{result['squad_need_contribution']}"
    )

    print(
        f"\nPerformance Reliability: "
        f"{result['performance_reliability']}%"
    )

    print(
        "\n"
        + "-" * 88
    )

    # =====================================================
    # TACTICAL EXPLANATION
    # =====================================================

    tactical_details = (
        result[
            "tactical_details"
        ]
    )

    strongest_tactical = (
        tactical_details.loc[
            tactical_details[
                "similarity"
            ].idxmax()
        ]
    )

    weakest_tactical = (
        tactical_details.loc[
            tactical_details[
                "similarity"
            ].idxmin()
        ]
    )

    print(
        "\nStrongest tactical alignment:"
    )

    print(
        strongest_tactical[
            "metric"
        ]
        .replace(
            "_",
            " ",
        )
        .title(),
        f"({strongest_tactical['similarity']}/100)"
    )

    print(
        "\nBiggest tactical mismatch:"
    )

    print(
        weakest_tactical[
            "metric"
        ]
        .replace(
            "_",
            " ",
        )
        .title(),
        f"({weakest_tactical['similarity']}/100)"
    )

    # =====================================================
    # POSITION EXPLANATION
    # =====================================================

    position_details = (
        result[
            "position_details"
        ]
    )

    if not position_details.empty:

        best_formation = (
            position_details.loc[
                position_details[
                    "formation_fit"
                ].idxmax()
            ]
        )

        main_formation = (
            position_details.loc[
                position_details[
                    "usage_percentage"
                ].idxmax()
            ]
        )

        print(
            "\nBest formation fit:"
        )

        print(
            f"{best_formation['formation']} "
            f"({best_formation['formation_fit']}/100)"
        )

        print(
            "\nFit in team's main formation:"
        )

        print(
            f"{main_formation['formation']} "
            f"({main_formation['formation_fit']}/100)"
        )

    # =====================================================
    # PERFORMANCE EXPLANATION
    # =====================================================

    performance_details = (
        result[
            "performance_details"
        ]
    )

    strongest_performance = (
        performance_details.loc[
            performance_details[
                "percentile"
            ].idxmax()
        ]
    )

    weakest_performance = (
        performance_details.loc[
            performance_details[
                "percentile"
            ].idxmin()
        ]
    )

    print(
        "\nStrongest performance area:"
    )

    print(
        strongest_performance[
            "metric"
        ]
        .replace(
            "_",
            " ",
        )
        .title(),
        f"({strongest_performance['percentile']} percentile)"
    )

    print(
        "\nWeakest performance area:"
    )

    print(
        weakest_performance[
            "metric"
        ]
        .replace(
            "_",
            " ",
        )
        .title(),
        f"({weakest_performance['percentile']} percentile)"
    )

    # =====================================================
    # POTENTIAL
    # =====================================================

    potential = (
        result[
            "potential_result"
        ]
    )

    print(
        "\nDevelopment runway:"
    )

    print(
        f"{potential['development_runway']} / 100"
    )

    print(
        "\nPerformance for age:"
    )

    print(
        f"{potential['performance_for_age']} percentile"
    )

    # =====================================================
    # SQUAD NEED
    # =====================================================

    squad = (
        result[
            "squad_best"
        ]
    )

    print(
        "\n"
        + "-" * 88
    )

    print(
        "\nSQUAD NEED ANALYSIS\n"
    )

    print(
        f"Best Squad Role: "
        f"{squad['role']}"
    )

    print(
        f"Squad Need: "
        f"{squad['squad_need']} / 100 "
        f"({squad_need_label(squad['squad_need'])})"
    )

    print(
        f"Formation Demand: "
        f"{squad['formation_demand']} / 100"
    )

    print(
        f"Depth Need: "
        f"{squad['depth_need']} / 100"
    )

    print(
        f"Quality Need: "
        f"{squad['quality_need']} / 100"
    )

    print(
        f"Upgrade Opportunity: "
        f"{squad['upgrade_opportunity']} / 100"
    )

    print(
        f"Candidate Role Fit: "
        f"{squad['candidate_compatibility']} / 100"
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
            "TransFit AI Transfer Fit V6"
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

    # =====================================================
    # POSITION / FORMATION DATA
    # =====================================================

    (
        position_players,
        formation_teams,
    ) = load_position_data()

    # =====================================================
    # PERFORMANCE DATA
    # =====================================================

    performance_players = (
        prepare_performance_data()
    )

    # =====================================================
    # RESOLVE PLAYER ONCE
    #
    # This also supports aliases such as:
    # Thiago / I. Thiago
    # Bruno Fernandes / B. Fernandes
    # =====================================================

    (
        performance_player,
        position_player,
    ) = resolve_candidate(
        performance_players,
        position_players,
        args.player,
    )

    player_id = int(
        performance_player[
            "player_id"
        ]
    )

    if (
        performance_player[
            "position_group"
        ]
        == "GK"
    ):
        raise SystemExit(
            "\nGoalkeeper Transfer Fit "
            "is not supported yet."
        )

    # =====================================================
    # TACTICAL
    # =====================================================

    (
        tactical_players,
        tactical_teams,
    ) = load_tactical_data()

    tactical_player = (
        find_player_by_id(
            tactical_players,
            player_id,
            "Tactical",
        )
    )

    tactical_team = (
        find_tactical_team(
            tactical_teams,
            args.team,
        )
    )

    # =====================================================
    # FORMATION TEAM
    # =====================================================

    formation_team = (
        find_formation_team(
            formation_teams,
            args.team,
        )
    )

    # =====================================================
    # POTENTIAL
    # =====================================================

    potential_players = (
        prepare_potential_data()
    )

    potential_player = (
        find_player_by_id(
            potential_players,
            player_id,
            "Potential",
        )
    )

    # =====================================================
    # SQUAD
    # =====================================================

    (
        raw_squad,
        _,
        _,
    ) = load_squad_data()

    squad = build_team_squad(
        raw_squad,
        position_players,
        performance_players,
        formation_team[
            "team"
        ],
        player_id,
    )

    # =====================================================
    # CALCULATE
    # =====================================================

    result = (
        calculate_transfer_fit_v5(
            tactical_player,
            tactical_team,
            position_player,
            formation_team,
            performance_player,
            potential_player,
            squad,
        )
    )

    # =====================================================
    # DISPLAY
    # =====================================================

    print_result(
        tactical_player,
        tactical_team,
        position_player,
        formation_team,
        result,
    )


if __name__ == "__main__":
    main()
