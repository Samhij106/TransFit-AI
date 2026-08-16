import argparse

from transfer_fit_engine import (
    load_data as load_tactical_data,
    find_player as find_tactical_player,
    find_team as find_tactical_team,
    calculate_tactical_fit,
)

from position_fit_engine import (
    load_data as load_position_data,
    find_player_by_id as find_position_player_by_id,
    find_team as find_formation_team,
    calculate_position_fit,
)

from performance_fit_engine import (
    load_data as load_performance_data,
    calculate_percentiles,
    find_player as find_performance_player,
    calculate_performance_score,
)

from age_potential_engine import (
    prepare_data as prepare_potential_data,
    calculate_potential,
)


# =========================================================
# TRANSFER FIT V4 WEIGHTS
# =========================================================

TACTICAL_WEIGHT = 0.40
POSITION_WEIGHT = 0.20
PERFORMANCE_WEIGHT = 0.25
POTENTIAL_WEIGHT = 0.15


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
# FIND POTENTIAL PLAYER
# =========================================================

def find_potential_player(players, player_name):
    query = player_name.strip().lower()

    exact = players[
        players["name"].astype(str).str.lower() == query
    ]

    if len(exact) == 1:
        return exact.iloc[0]

    partial = players[
        players["name"]
        .astype(str)
        .str.lower()
        .str.contains(query, regex=False)
    ]

    if len(partial) == 1:
        return partial.iloc[0]

    if len(partial) > 1:
        print("\nMultiple players found:\n")

        print(
            partial[
                [
                    "name",
                    "team",
                    "primary_position",
                ]
            ].to_string(index=False)
        )

        raise SystemExit(
            "\nPlease enter a more specific player name."
        )

    raise SystemExit(
        f"\nPlayer not found: {player_name}"
    )


# =========================================================
# CALCULATE TRANSFER FIT V4
# =========================================================

def calculate_transfer_fit_v4(
    tactical_player,
    tactical_team,
    position_player,
    formation_team,
    performance_player,
    potential_player,
):
    # -----------------------------------------------------
    # Tactical Fit
    # -----------------------------------------------------

    tactical_score, tactical_details = calculate_tactical_fit(
        tactical_player,
        tactical_team,
    )

    # -----------------------------------------------------
    # Position Fit
    # -----------------------------------------------------

    position_score, position_details = calculate_position_fit(
        position_player,
        formation_team,
    )

    # -----------------------------------------------------
    # Performance
    # -----------------------------------------------------

    performance_result = calculate_performance_score(
        performance_player
    )

    performance_score = performance_result[
        "performance_score"
    ]

    # -----------------------------------------------------
    # Potential
    # -----------------------------------------------------

    potential_result = calculate_potential(
        potential_player
    )

    potential_score = potential_result[
        "potential_score"
    ]

    # -----------------------------------------------------
    # Contributions
    # -----------------------------------------------------

    tactical_contribution = (
        tactical_score * TACTICAL_WEIGHT
    )

    position_contribution = (
        position_score * POSITION_WEIGHT
    )

    performance_contribution = (
        performance_score * PERFORMANCE_WEIGHT
    )

    potential_contribution = (
        potential_score * POTENTIAL_WEIGHT
    )

    final_score = (
        tactical_contribution
        + position_contribution
        + performance_contribution
        + potential_contribution
    )

    return {
        "final_score": round(final_score, 1),

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

        "potential_score": round(
            potential_score,
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

        "potential_contribution": round(
            potential_contribution,
            2,
        ),

        "tactical_details": tactical_details,
        "position_details": position_details,
        "performance_details": performance_result[
            "details"
        ],

        "performance_reliability": performance_result[
            "reliability"
        ],

        "potential_result": potential_result,
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
    print("\n" + "=" * 84)

    print(
        "TRANSFIT AI - TRANSFER FIT V4"
    )

    print("=" * 84)

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

    secondary = position_player.get(
        "secondary_position"
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

    print("\n" + "-" * 84)

    print(
        f"\nFINAL TRANSFER FIT: "
        f"{result['final_score']} / 100"
    )

    print(
        f"Classification: "
        f"{transfer_fit_label(result['final_score'])}"
    )

    print("\n" + "-" * 84)

    print("\nSCORE BREAKDOWN\n")

    print(
        f"Tactical Fit: "
        f"{result['tactical_score']} / 100 "
        f"x {int(TACTICAL_WEIGHT * 100)}% "
        f"= {result['tactical_contribution']}"
    )

    print(
        f"Position Fit: "
        f"{result['position_score']} / 100 "
        f"x {int(POSITION_WEIGHT * 100)}% "
        f"= {result['position_contribution']}"
    )

    print(
        f"Performance:  "
        f"{result['performance_score']} / 100 "
        f"x {int(PERFORMANCE_WEIGHT * 100)}% "
        f"= {result['performance_contribution']}"
    )

    print(
        f"Potential:    "
        f"{result['potential_score']} / 100 "
        f"x {int(POTENTIAL_WEIGHT * 100)}% "
        f"= {result['potential_contribution']}"
    )

    print(
        f"\nPerformance Reliability: "
        f"{result['performance_reliability']}%"
    )

    print("\n" + "-" * 84)

    # -----------------------------------------------------
    # Tactical explanation
    # -----------------------------------------------------

    tactical_details = result[
        "tactical_details"
    ]

    strongest_tactical = tactical_details.loc[
        tactical_details[
            "similarity"
        ].idxmax()
    ]

    weakest_tactical = tactical_details.loc[
        tactical_details[
            "similarity"
        ].idxmin()
    ]

    print(
        "\nStrongest tactical alignment:"
    )

    print(
        strongest_tactical["metric"]
        .replace("_", " ")
        .title(),
        f"({strongest_tactical['similarity']}/100)"
    )

    print(
        "\nBiggest tactical mismatch:"
    )

    print(
        weakest_tactical["metric"]
        .replace("_", " ")
        .title(),
        f"({weakest_tactical['similarity']}/100)"
    )

    # -----------------------------------------------------
    # Position explanation
    # -----------------------------------------------------

    position_details = result[
        "position_details"
    ]

    if not position_details.empty:
        best_formation = position_details.loc[
            position_details[
                "formation_fit"
            ].idxmax()
        ]

        main_formation = position_details.loc[
            position_details[
                "usage_percentage"
            ].idxmax()
        ]

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

    # -----------------------------------------------------
    # Performance explanation
    # -----------------------------------------------------

    performance_details = result[
        "performance_details"
    ]

    strongest_performance = performance_details.loc[
        performance_details[
            "percentile"
        ].idxmax()
    ]

    weakest_performance = performance_details.loc[
        performance_details[
            "percentile"
        ].idxmin()
    ]

    print(
        "\nStrongest performance area:"
    )

    print(
        strongest_performance["metric"]
        .replace("_", " ")
        .title(),
        f"({strongest_performance['percentile']} percentile)"
    )

    print(
        "\nWeakest performance area:"
    )

    print(
        weakest_performance["metric"]
        .replace("_", " ")
        .title(),
        f"({weakest_performance['percentile']} percentile)"
    )

    # -----------------------------------------------------
    # Potential explanation
    # -----------------------------------------------------

    potential = result[
        "potential_result"
    ]

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

    print("\n" + "=" * 84)


# =========================================================
# MAIN
# =========================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "TransFit AI Transfer Fit V4"
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
    # Tactical
    # -----------------------------------------------------

    tactical_players, tactical_teams = (
        load_tactical_data()
    )

    tactical_player = find_tactical_player(
        tactical_players,
        args.player,
    )

    tactical_team = find_tactical_team(
        tactical_teams,
        args.team,
    )

    # -----------------------------------------------------
    # Position
    # -----------------------------------------------------

    position_players, formation_teams = (
        load_position_data()
    )

    position_player = find_position_player_by_id(
    position_players,
    tactical_player["player_id"],
)
    
    formation_team = find_formation_team(
        formation_teams,
        args.team,
    )

    # -----------------------------------------------------
    # Performance
    # -----------------------------------------------------

    performance_players = load_performance_data()

    performance_players = calculate_percentiles(
        performance_players
    )

    performance_player = find_performance_player(
        performance_players,
        args.player,
    )

    # -----------------------------------------------------
    # Potential
    # -----------------------------------------------------

    potential_players = prepare_potential_data()

    potential_player = find_potential_player(
        potential_players,
        args.player,
    )

    # -----------------------------------------------------
    # Calculate
    # -----------------------------------------------------

    result = calculate_transfer_fit_v4(
        tactical_player,
        tactical_team,
        position_player,
        formation_team,
        performance_player,
        potential_player,
    )

    # -----------------------------------------------------
    # Display
    # -----------------------------------------------------

    print_result(
        tactical_player,
        tactical_team,
        position_player,
        formation_team,
        result,
    )


if __name__ == "__main__":
    main()