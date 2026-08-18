import argparse
import pandas as pd


RAW_PLAYER_FILE = "data/processed/player_profiles_season_2025.csv"
TACTICAL_PLAYER_FILE = "data/processed/player_tactical_profiles_2025.csv"
REALISM_PLAYER_FILE = (
    "data/processed/"
    "player_realism_profiles_2025.csv"
)

FULL_RELIABILITY_MINUTES = 900


# =========================================================
# PERFORMANCE WEIGHTS BY POSITION GROUP
# =========================================================

PERFORMANCE_WEIGHTS = {
    "CB": {
        "rating": 0.25,
        "tackles_per90": 0.20,
        "interceptions_per90": 0.25,
        "passes_per90": 0.20,
        "goals_per90": 0.05,
        "key_passes_per90": 0.05,
    },

    "FB": {
        "rating": 0.20,
        "tackles_per90": 0.15,
        "interceptions_per90": 0.10,
        "passes_per90": 0.15,
        "key_passes_per90": 0.15,
        "assists_per90": 0.10,
        "successful_dribbles_per90": 0.10,
        "dribble_success_rate": 0.05,
    },

    "DM": {
        "rating": 0.20,
        "tackles_per90": 0.20,
        "interceptions_per90": 0.20,
        "passes_per90": 0.20,
        "key_passes_per90": 0.10,
        "assists_per90": 0.05,
        "successful_dribbles_per90": 0.05,
    },

    "CM": {
        "rating": 0.20,
        "passes_per90": 0.20,
        "key_passes_per90": 0.20,
        "assists_per90": 0.10,
        "tackles_per90": 0.10,
        "interceptions_per90": 0.10,
        "successful_dribbles_per90": 0.10,
    },

    "AM": {
        "rating": 0.15,
        "key_passes_per90": 0.23,
        "assists_per90": 0.15,
        "goals": 0.15,
        "goals_per90": 0.05,
        "shots_on_target_per90": 0.07,
        "successful_dribbles_per90": 0.12,
        "dribble_success_rate": 0.08,
    },

    "W": {
        "rating": 0.15,
        "goals": 0.20,
        "goals_per90": 0.08,
        "assists_per90": 0.15,
        "shots_on_target_per90": 0.12,
        "key_passes_per90": 0.15,
        "successful_dribbles_per90": 0.10,
        "dribble_success_rate": 0.05,
    },

    "FW": {
        "rating": 0.15,
        "goals": 0.25,
        "goals_per90": 0.10,
        "shots_on_target_per90": 0.15,
        "shot_accuracy": 0.12,
        "shots_per90": 0.08,
        "assists_per90": 0.10,
        "key_passes_per90": 0.05,
    },
}


# =========================================================
# LOAD DATA
# =========================================================

def load_data():
    raw = pd.read_csv(RAW_PLAYER_FILE)

    tactical = pd.read_csv(
        TACTICAL_PLAYER_FILE
    )[[
        "player_id",
        "position_group",
    ]]

    df = raw.merge(
        tactical,
        on="player_id",
        how="left",
    )

    try:
        verified = pd.read_csv(
            REALISM_PLAYER_FILE
        )[[
            "api_football_player_id",
            "verified_position_group",
        ]].rename(columns={
            "api_football_player_id": "player_id"
        })
    except FileNotFoundError:
        verified = None

    if verified is not None:
        df = df.merge(
            verified,
            on="player_id",
            how="left",
        )
        has_verified_group = df[
            "verified_position_group"
        ].notna()
        df.loc[
            has_verified_group,
            "position_group",
        ] = df.loc[
            has_verified_group,
            "verified_position_group",
        ]

    return df


# =========================================================
# FIND PLAYER
# =========================================================

def find_player(players, player_name):
    query = player_name.strip().lower()

    exact = players[
        players["name"]
        .astype(str)
        .str.lower()
        == query
    ]

    if len(exact) == 1:
        return exact.iloc[0]

    partial = players[
        players["name"]
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
# PERCENTILE BY POSITION
# =========================================================

def calculate_percentiles(players):
    metrics = set()

    for weights in PERFORMANCE_WEIGHTS.values():
        metrics.update(weights.keys())

    for metric in metrics:
        players[metric] = pd.to_numeric(
            players[metric],
            errors="coerce",
        ).fillna(0)

        players[f"{metric}_pct"] = (
            players.groupby("position_group")[metric]
            .rank(
                pct=True,
                method="average",
            )
            * 100
        )

    return players


# =========================================================
# MINUTES RELIABILITY
# =========================================================

def minutes_reliability(minutes):
    minutes = pd.to_numeric(
        minutes,
        errors="coerce",
    )

    if pd.isna(minutes):
        minutes = 0

    reliability = (
        float(minutes)
        / FULL_RELIABILITY_MINUTES
    )

    return max(
        0,
        min(1, reliability),
    )


# =========================================================
# PERFORMANCE SCORE
# =========================================================

def calculate_performance_score(
    player,
):
    group = player["position_group"]

    if group == "GK":
        raise SystemExit(
            "\nGoalkeeper performance scoring "
            "is not supported yet."
        )

    if group not in PERFORMANCE_WEIGHTS:
        raise SystemExit(
            f"\nUnsupported position group: {group}"
        )

    weights = PERFORMANCE_WEIGHTS[group]

    details = []

    raw_score = 0

    for metric, weight in weights.items():
        percentile = float(
            player[f"{metric}_pct"]
        )

        raw_value = float(
            player[metric]
        )

        contribution = (
            percentile * weight
        )

        raw_score += contribution

        details.append({
            "metric": metric,
            "raw_value": round(
                raw_value,
                2,
            ),
            "percentile": round(
                percentile,
                1,
            ),
            "weight": round(
                weight * 100,
                1,
            ),
            "contribution": round(
                contribution,
                2,
            ),
        })

    reliability = minutes_reliability(
        player["minutes"]
    )

    # Low-minute players are regressed toward 50.
    adjusted_score = (
        50
        + reliability
        * (raw_score - 50)
    )

    adjusted_score = max(
        0,
        min(100, adjusted_score),
    )

    return {
        "raw_score": round(
            raw_score,
            1,
        ),
        "performance_score": round(
            adjusted_score,
            1,
        ),
        "reliability": round(
            reliability * 100,
            1,
        ),
        "details": pd.DataFrame(
            details
        ),
    }


# =========================================================
# LABEL
# =========================================================

def performance_label(score):
    if score >= 85:
        return "Elite Performance"

    if score >= 75:
        return "Strong Performance"

    if score >= 65:
        return "Good Performance"

    if score >= 50:
        return "Average Performance"

    return "Below Average Performance"


# =========================================================
# DISPLAY
# =========================================================

def print_result(
    player,
    result,
):
    print("\n" + "=" * 82)

    print(
        "TRANSFIT AI - PERFORMANCE QUALITY ANALYSIS"
    )

    print("=" * 82)

    print(
        f"\nPlayer:         "
        f"{player['name']}"
    )

    print(
        f"Team:           "
        f"{player['team']}"
    )

    print(
        f"Position:       "
        f"{player['primary_position']}"
    )

    print(
        f"Position Group: "
        f"{player['position_group']}"
    )

    print(
        f"Minutes:        "
        f"{player['minutes']}"
    )

    print(
        f"Reliability:    "
        f"{result['reliability']}%"
    )

    print("\n" + "-" * 82)

    print(
        f"\nPERFORMANCE SCORE: "
        f"{result['performance_score']} / 100"
    )

    print(
        f"Classification: "
        f"{performance_label(result['performance_score'])}"
    )

    print(
        f"Raw percentile score: "
        f"{result['raw_score']} / 100"
    )

    print("\n" + "-" * 82)

    display = result[
        "details"
    ].copy()

    display["metric"] = (
        display["metric"]
        .str.replace("_", " ")
        .str.title()
    )

    display = display.rename(
        columns={
            "metric": "Metric",
            "raw_value": "Value",
            "percentile": "Percentile",
            "weight": "Weight %",
            "contribution": "Contribution",
        }
    )

    print(
        "\n"
        + display[
            [
                "Metric",
                "Value",
                "Percentile",
                "Weight %",
                "Contribution",
            ]
        ].to_string(index=False)
    )

    strongest = result["details"].loc[
        result["details"][
            "percentile"
        ].idxmax()
    ]

    weakest = result["details"].loc[
        result["details"][
            "percentile"
        ].idxmin()
    ]

    print("\n" + "-" * 82)

    print(
        "\nStrongest performance area:"
    )

    print(
        strongest["metric"]
        .replace("_", " ")
        .title(),
        f"({strongest['percentile']} percentile)"
    )

    print(
        "\nWeakest performance area:"
    )

    print(
        weakest["metric"]
        .replace("_", " ")
        .title(),
        f"({weakest['percentile']} percentile)"
    )

    print("\n" + "=" * 82)


# =========================================================
# MAIN
# =========================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "TransFit AI Performance Quality Engine"
        )
    )

    parser.add_argument(
        "player",
        help="Player name",
    )

    args = parser.parse_args()

    players = load_data()

    players = calculate_percentiles(
        players
    )

    player = find_player(
        players,
        args.player,
    )

    result = calculate_performance_score(
        player
    )

    print_result(
        player,
        result,
    )


if __name__ == "__main__":
    main()
