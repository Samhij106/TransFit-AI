import argparse

from transfer_fit_engine import (
    load_data as load_tactical_data,
    find_player as find_tactical_player,
    find_team as find_tactical_team,
    calculate_tactical_fit,
)

from position_fit_engine import (
    load_data as load_position_data,
    find_player as find_position_player,
    find_team as find_formation_team,
    calculate_position_fit,
)

from performance_fit_engine import (
    load_data as load_performance_data,
    calculate_percentiles,
    find_player as find_performance_player,
    calculate_performance_score,
)


# =========================================================
# TRANSFER FIT V3 WEIGHTS
# =========================================================

TACTICAL_WEIGHT = 0.45
POSITION_WEIGHT = 0.25
PERFORMANCE_WEIGHT = 0.30


# =========================================================
# FINAL LABEL
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
# CALCULATE TRANSFER FIT V3
# =========================================================

def calculate_transfer_fit_v3(
    tactical_player,
    tactical_team,
    position_player,
    formation_team,
    performance_player,
):
    # Tactical
    tactical_score, tactical_details = calculate_tactical_fit(
        tactical_player,
        tactical_team,
    )

    # Position
    position_score, position_details = calculate_position_fit(
        position_player,
        formation_team,
    )

    # Performance
    performance_result = calculate_performance_score(
        performance_player
    )

    performance_score = performance_result[
        "performance_score"
    ]

    # Contributions
    tactical_contribution = (
        tactical_score * TACTICAL_WEIGHT
    )

    position_contribution = (
        position_score * POSITION_WEIGHT
    )

    performance_contribution = (
        performance_score * PERFORMANCE_WEIGHT
    )

    final_score = (
        tactical_contribution
        + position_contribution
        + performance_contribution
    )

    return {
        "final_score": round(final_score, 1),

        "tactical_score": round(tactical_score, 1),
        "position_score": round(position_score, 1),
        "performance_score": round(performance_score, 1),

        "tactical_contribution": round(
            tactical_contribution, 2
        ),

        "position_contribution": round(
            position_contribution, 2
        ),

        "performance_contribution": round(
            performance_contribution, 2
        ),

        "tactical_details": tactical_details,
        "position_details": position_details,
        "performance_details": performance_result["details"],

        "performance_reliability": performance_result[
            "reliability"
        ],
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
    print("\n" + "=" * 82)
    print("TRANSFIT AI - TRANSFER FIT V3")
    print("=" * 82)

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
        f"Formation:    "
        f"{formation_team['primary_formation']}"
    )

    print("\n" + "-" * 82)

    print(
        f"\nFINAL TRANSFER FIT: "
        f"{result['final_score']} / 100"
    )

    print(
        f"Classification: "
        f"{transfer_fit_label(result['final_score'])}"
    )

    print("\n" + "-" * 82)

    print("\nSCORE BREAKDOWN\n")

    print(
        f"Tactical Fit:    "
        f"{result['tactical_score']} / 100 "
        f"x {int(TACTICAL_WEIGHT * 100)}% "
        f"= {result['tactical_contribution']}"
    )

    print(
        f"Position Fit:    "
        f"{result['position_score']} / 100 "
        f"x {int(POSITION_WEIGHT * 100)}% "
        f"= {result['position_contribution']}"
    )

    print(
        f"Performance:     "
        f"{result['performance_score']} / 100 "
        f"x {int(PERFORMANCE_WEIGHT * 100)}% "
        f"= {result['performance_contribution']}"
    )

    print(
        f"Performance Reliability: "
        f"{result['performance_reliability']}%"
    )

    print("\n" + "-" * 82)

    # Tactical explanation
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

    print("\nStrongest tactical alignment:")

    print(
        strongest_tactical["metric"]
        .replace("_", " ")
        .title(),
        f"({strongest_tactical['similarity']}/100)"
    )

    print("\nBiggest tactical mismatch:")

    print(
        weakest_tactical["metric"]
        .replace("_", " ")
        .title(),
        f"({weakest_tactical['similarity']}/100)"
    )

    # Position explanation
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

        print("\nBest formation fit:")

        print(
            f"{best_formation['formation']} "
            f"({best_formation['formation_fit']}/100)"
        )

        print("\nFit in team's main formation:")

        print(
            f"{main_formation['formation']} "
            f"({main_formation['formation_fit']}/100)"
        )

    # Performance explanation
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

    print("\nStrongest performance area:")

    print(
        strongest_performance["metric"]
        .replace("_", " ")
        .title(),
        f"({strongest_performance['percentile']} percentile)"
    )

    print("\nWeakest performance area:")

    print(
        weakest_performance["metric"]
        .replace("_", " ")
        .title(),
        f"({weakest_performance['percentile']} percentile)"
    )

    print("\n" + "=" * 82)


# =========================================================
# MAIN
# =========================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "TransFit AI Transfer Fit V3"
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
    # Tactical data
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
    # Position data
    # -----------------------------------------------------

    position_players, formation_teams = (
        load_position_data()
    )

    position_player = find_position_player(
        position_players,
        args.player,
    )

    formation_team = find_formation_team(
        formation_teams,
        args.team,
    )

    # -----------------------------------------------------
    # Performance data
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
    # Calculate
    # -----------------------------------------------------

    result = calculate_transfer_fit_v3(
        tactical_player,
        tactical_team,
        position_player,
        formation_team,
        performance_player,
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