import argparse
import pandas as pd

from performance_fit_engine import (
    load_data,
    calculate_percentiles,
    calculate_performance_score,
    find_player,
)


# =========================================================
# DEVELOPMENT RUNWAY
# =========================================================

def development_runway(age):
    """
    Age-based development runway.

    This is NOT a prediction of true football potential.
    It represents how much development runway a player
    is likely to have based on age.
    """

    age = pd.to_numeric(age, errors="coerce")

    if pd.isna(age):
        return 50.0

    age = float(age)

    if age <= 20:
        return 100.0
    if age == 21:
        return 96.0
    if age == 22:
        return 91.0
    if age == 23:
        return 85.0
    if age == 24:
        return 78.0
    if age == 25:
        return 70.0
    if age == 26:
        return 62.0
    if age == 27:
        return 54.0
    if age == 28:
        return 46.0
    if age == 29:
        return 38.0
    if age == 30:
        return 30.0
    if age == 31:
        return 23.0
    if age == 32:
        return 17.0

    return 10.0


# =========================================================
# AGE BANDS
# =========================================================

def age_band(age):
    age = pd.to_numeric(age, errors="coerce")

    if pd.isna(age):
        return "unknown"

    age = float(age)

    if age <= 21:
        return "U21"

    if age <= 24:
        return "22-24"

    if age <= 27:
        return "25-27"

    if age <= 30:
        return "28-30"

    return "31+"


# =========================================================
# PREPARE DATASET
# =========================================================

def prepare_data():
    players = load_data()

    players = calculate_percentiles(
        players
    )

    # Goalkeepers are still excluded because our
    # performance model does not support them yet.
    players = players[
        players["position_group"] != "GK"
    ].copy()

    # -----------------------------------------------------
    # Current performance score for every player
    # -----------------------------------------------------

    players["performance_score"] = players.apply(
        lambda row: calculate_performance_score(
            row
        )["performance_score"],
        axis=1,
    )

    players["age"] = pd.to_numeric(
        players["age"],
        errors="coerce",
    )

    players["age_band"] = players[
        "age"
    ].apply(age_band)

    # -----------------------------------------------------
    # Performance percentile within position + age band
    # -----------------------------------------------------

    players["performance_for_age"] = 0.0

    for (
        position_group,
        band
    ), indexes in players.groupby(
        [
            "position_group",
            "age_band",
        ]
    ).groups.items():

        group = players.loc[
            indexes,
            "performance_score",
        ]

        # If the age-position group is too small,
        # compare against the whole position group.
        if len(group) < 5:
            position_indexes = players[
                players["position_group"]
                == position_group
            ].index

            ranked = players.loc[
                position_indexes,
                "performance_score",
            ].rank(
                pct=True,
                method="average",
            ) * 100

            players.loc[
                indexes,
                "performance_for_age",
            ] = ranked.loc[indexes]

        else:
            players.loc[
                indexes,
                "performance_for_age",
            ] = (
                group.rank(
                    pct=True,
                    method="average",
                )
                * 100
            )

    return players


# =========================================================
# POTENTIAL PROXY
# =========================================================

def calculate_potential(player):
    age = float(
        player["age"]
    )

    runway = development_runway(
        age
    )

    performance_for_age = float(
        player["performance_for_age"]
    )

    # -----------------------------------------------------
    # Potential proxy
    #
    # 65% development runway
    # 35% performance relative to similar-aged players
    # -----------------------------------------------------

    potential_score = (
        runway * 0.65
        + performance_for_age * 0.35
    )

    potential_score = max(
        0,
        min(100, potential_score),
    )

    return {
        "age": round(age, 1),
        "age_band": player["age_band"],
        "development_runway": round(
            runway,
            1,
        ),
        "performance_score": round(
            float(player["performance_score"]),
            1,
        ),
        "performance_for_age": round(
            performance_for_age,
            1,
        ),
        "potential_score": round(
            potential_score,
            1,
        ),
    }


# =========================================================
# LABEL
# =========================================================

def potential_label(score):
    if score >= 85:
        return "Exceptional Development Upside"

    if score >= 75:
        return "High Development Upside"

    if score >= 65:
        return "Good Development Upside"

    if score >= 50:
        return "Moderate Development Upside"

    return "Limited Development Upside"


# =========================================================
# DISPLAY
# =========================================================

def print_result(
    player,
    result,
):
    print("\n" + "=" * 82)

    print(
        "TRANSFIT AI - AGE & POTENTIAL ANALYSIS"
    )

    print("=" * 82)

    print(
        f"\nPlayer:          "
        f"{player['name']}"
    )

    print(
        f"Team:            "
        f"{player['team']}"
    )

    print(
        f"Position:        "
        f"{player['primary_position']}"
    )

    print(
        f"Position Group:  "
        f"{player['position_group']}"
    )

    print(
        f"Age:             "
        f"{result['age']}"
    )

    print(
        f"Age Band:        "
        f"{result['age_band']}"
    )

    print("\n" + "-" * 82)

    print(
        f"\nPOTENTIAL PROXY SCORE: "
        f"{result['potential_score']} / 100"
    )

    print(
        f"Classification: "
        f"{potential_label(result['potential_score'])}"
    )

    print("\n" + "-" * 82)

    print("\nSCORE BREAKDOWN\n")

    print(
        f"Development Runway:    "
        f"{result['development_runway']} / 100"
    )

    print(
        f"Current Performance:   "
        f"{result['performance_score']} / 100"
    )

    print(
        f"Performance For Age:   "
        f"{result['performance_for_age']} percentile"
    )

    print("\nFormula:")

    print(
        f"{result['development_runway']} x 65% "
        f"+ {result['performance_for_age']} x 35%"
    )

    print("\n" + "-" * 82)

    print(
        "\nNote: This is a data-driven development "
        "potential proxy, not a direct prediction "
        "of a player's true future ability."
    )

    print("\n" + "=" * 82)


# =========================================================
# MAIN
# =========================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "TransFit AI Age & Potential Engine"
        )
    )

    parser.add_argument(
        "player",
        help="Player name",
    )

    args = parser.parse_args()

    players = prepare_data()

    player = find_player(
        players,
        args.player,
    )

    result = calculate_potential(
        player
    )

    print_result(
        player,
        result,
    )


if __name__ == "__main__":
    main()