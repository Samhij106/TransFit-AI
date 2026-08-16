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


# =========================================================
# TRANSFER FIT WEIGHTS
# =========================================================

TACTICAL_WEIGHT = 0.65
POSITION_WEIGHT = 0.35


# =========================================================
# FINAL FIT LABEL
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
# CALCULATE FINAL TRANSFER FIT
# =========================================================

def calculate_transfer_fit(
    tactical_player,
    tactical_team,
    position_player,
    formation_team,
):
    tactical_score, tactical_details = calculate_tactical_fit(
        tactical_player,
        tactical_team,
    )

    position_score, position_details = calculate_position_fit(
        position_player,
        formation_team,
    )

    tactical_contribution = (
        tactical_score * TACTICAL_WEIGHT
    )

    position_contribution = (
        position_score * POSITION_WEIGHT
    )

    final_score = (
        tactical_contribution
        + position_contribution
    )

    return {
        "final_score": round(final_score, 1),
        "tactical_score": round(tactical_score, 1),
        "position_score": round(position_score, 1),
        "tactical_contribution": round(
            tactical_contribution,
            2,
        ),
        "position_contribution": round(
            position_contribution,
            2,
        ),
        "tactical_details": tactical_details,
        "position_details": position_details,
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
    print("\n" + "=" * 78)

    print(
        "TRANSFIT AI - TRANSFER FIT V2"
    )

    print("=" * 78)

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
        f"Secondary:    "
        f"{secondary}"
    )

    print(
        f"Formation:    "
        f"{formation_team['primary_formation']}"
    )

    print("\n" + "-" * 78)

    print(
        f"\nFINAL TRANSFER FIT: "
        f"{result['final_score']} / 100"
    )

    print(
        f"Classification: "
        f"{transfer_fit_label(result['final_score'])}"
    )

    print("\n" + "-" * 78)

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

    print("\n" + "-" * 78)


    # -----------------------------------------------------
    # Tactical strengths / weaknesses
    # -----------------------------------------------------

    tactical_details = result[
        "tactical_details"
    ]

    strongest = tactical_details.loc[
        tactical_details["similarity"].idxmax()
    ]

    weakest = tactical_details.loc[
        tactical_details["similarity"].idxmin()
    ]

    print(
        "\nStrongest tactical alignment:"
    )

    print(
        strongest["metric"]
        .replace("_", " ")
        .title(),
        f"({strongest['similarity']}/100)"
    )

    print(
        "\nBiggest tactical mismatch:"
    )

    print(
        weakest["metric"]
        .replace("_", " ")
        .title(),
        f"({weakest['similarity']}/100)"
    )


    # -----------------------------------------------------
    # Formation information
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

    print("\n" + "=" * 78)


# =========================================================
# MAIN
# =========================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "TransFit AI Combined Transfer Fit Engine"
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
    # Position / formation data
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
    # Calculate
    # -----------------------------------------------------

    result = calculate_transfer_fit(
        tactical_player,
        tactical_team,
        position_player,
        formation_team,
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