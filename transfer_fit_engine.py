import argparse
import pandas as pd


PLAYER_FILE = "data/processed/player_tactical_profiles_2025.csv"
TEAM_FILE = "data/processed/team_tactical_profiles_2025.csv"


TACTICAL_COLUMNS = [
    "possession_control",
    "passing_control",
    "chance_creation",
    "attacking_pressure",
    "directness",
    "shooting_efficiency",
]


# ---------------------------------------------------------
# Position-specific tactical importance
# ---------------------------------------------------------

POSITION_WEIGHTS = {
    "CB": {
        "possession_control": 0.34,
        "passing_control": 0.31,
        "chance_creation": 0.05,
        "attacking_pressure": 0.05,
        "directness": 0.20,
        "shooting_efficiency": 0.05,
    },

    "FB": {
        "possession_control": 0.23,
        "passing_control": 0.20,
        "chance_creation": 0.15,
        "attacking_pressure": 0.12,
        "directness": 0.25,
        "shooting_efficiency": 0.05,
    },

    "DM": {
        "possession_control": 0.30,
        "passing_control": 0.30,
        "chance_creation": 0.12,
        "attacking_pressure": 0.08,
        "directness": 0.15,
        "shooting_efficiency": 0.05,
    },

    "CM": {
        "possession_control": 0.25,
        "passing_control": 0.28,
        "chance_creation": 0.20,
        "attacking_pressure": 0.10,
        "directness": 0.12,
        "shooting_efficiency": 0.05,
    },

    "AM": {
        "possession_control": 0.15,
        "passing_control": 0.22,
        "chance_creation": 0.25,
        "attacking_pressure": 0.15,
        "directness": 0.13,
        "shooting_efficiency": 0.10,
    },

    "W": {
        "possession_control": 0.14,
        "passing_control": 0.12,
        "chance_creation": 0.18,
        "attacking_pressure": 0.22,
        "directness": 0.21,
        "shooting_efficiency": 0.13,
    },

    "FW": {
        "possession_control": 0.08,
        "passing_control": 0.08,
        "chance_creation": 0.10,
        "attacking_pressure": 0.25,
        "directness": 0.18,
        "shooting_efficiency": 0.31,
    },
}


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

def load_data():
    players = pd.read_csv(PLAYER_FILE)
    teams = pd.read_csv(TEAM_FILE)

    return players, teams


# ---------------------------------------------------------
# Find player
# ---------------------------------------------------------

def find_player(players, player_name):
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
        names = partial[["name", "team", "primary_position"]]

        print("\nMultiple players found:\n")
        print(names.to_string(index=False))

        raise SystemExit(
            "\nPlease enter a more specific player name."
        )

    raise SystemExit(
        f"\nPlayer not found: {player_name}"
    )


# ---------------------------------------------------------
# Find team
# ---------------------------------------------------------

def find_team(teams, team_name):
    query = team_name.strip().lower()

    exact = teams[
        teams["team"].astype(str).str.lower() == query
    ]

    if len(exact) == 1:
        return exact.iloc[0]

    partial = teams[
        teams["team"]
        .astype(str)
        .str.lower()
        .str.contains(query, regex=False)
    ]

    if len(partial) == 1:
        return partial.iloc[0]

    if len(partial) > 1:
        print("\nMultiple teams found:\n")
        print(partial["team"].to_string(index=False))

        raise SystemExit(
            "\nPlease enter a more specific team name."
        )

    raise SystemExit(
        f"\nTeam not found: {team_name}"
    )


# ---------------------------------------------------------
# Fit label
# ---------------------------------------------------------

def fit_label(score):
    if score >= 90:
        return "Elite Tactical Fit"

    if score >= 80:
        return "Strong Tactical Fit"

    if score >= 70:
        return "Good Tactical Fit"

    if score >= 60:
        return "Moderate Tactical Fit"

    return "Low Tactical Fit"


# ---------------------------------------------------------
# Tactical fit calculation
# ---------------------------------------------------------

def calculate_tactical_fit(player, team):
    position_group = player["position_group"]

    if position_group == "GK":
        raise SystemExit(
            "\nGoalkeeper tactical fit is not supported yet."
        )

    if position_group not in POSITION_WEIGHTS:
        raise SystemExit(
            f"\nUnsupported position group: {position_group}"
        )

    weights = POSITION_WEIGHTS[position_group]

    details = []

    total_score = 0

    for metric in TACTICAL_COLUMNS:
        player_score = float(player[metric])
        team_score = float(team[metric])

        difference = abs(player_score - team_score)

        similarity = max(
            0,
            100 - difference
        )

        weight = weights[metric]

        weighted_score = similarity * weight

        total_score += weighted_score

        details.append({
            "metric": metric,
            "player_score": round(player_score, 1),
            "team_score": round(team_score, 1),
            "difference": round(difference, 1),
            "similarity": round(similarity, 1),
            "weight": round(weight * 100, 1),
            "weighted_score": round(weighted_score, 2),
        })

    return round(total_score, 1), pd.DataFrame(details)


# ---------------------------------------------------------
# Display result
# ---------------------------------------------------------

def print_result(player, team, fit_score, details):
    print("\n" + "=" * 75)
    print("TRANSFIT AI - TACTICAL FIT ANALYSIS")
    print("=" * 75)

    print(f"\nPlayer:       {player['name']}")
    print(f"Current Team: {player['team']}")
    print(f"Target Team:  {team['team']}")
    print(f"Position:     {player['primary_position']}")
    print(f"Group:        {player['position_group']}")

    print("\n" + "-" * 75)

    print(
        f"\nTACTICAL FIT SCORE: "
        f"{fit_score} / 100"
    )

    print(
        f"Classification: {fit_label(fit_score)}"
    )

    print("\n" + "-" * 75)

    display = details.copy()

    display["metric"] = (
        display["metric"]
        .str.replace("_", " ")
        .str.title()
    )

    display = display.rename(columns={
        "metric": "Metric",
        "player_score": "Player",
        "team_score": "Team",
        "similarity": "Fit",
        "weight": "Weight %",
    })

    print(
        "\n" +
        display[
            [
                "Metric",
                "Player",
                "Team",
                "Fit",
                "Weight %",
            ]
        ].to_string(index=False)
    )

    relevant = details[
        details["weight"] > 0
    ]

    strongest = relevant.loc[
        relevant["similarity"].idxmax()
    ]

    weakest = relevant.loc[
        relevant["similarity"].idxmin()
    ]

    print("\n" + "-" * 75)

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

    print("\n" + "=" * 75)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="TransFit AI Tactical Fit Engine"
    )

    parser.add_argument(
        "player",
        help="Player name"
    )

    parser.add_argument(
        "team",
        help="Target team"
    )

    args = parser.parse_args()

    players, teams = load_data()

    player = find_player(
        players,
        args.player
    )

    team = find_team(
        teams,
        args.team
    )

    fit_score, details = calculate_tactical_fit(
        player,
        team
    )

    print_result(
        player,
        team,
        fit_score,
        details
    )


if __name__ == "__main__":
    main()