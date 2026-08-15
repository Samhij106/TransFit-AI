import pandas as pd

DATA_FILE = "data/processed/player_profiles_2024.csv"

df = pd.read_csv(DATA_FILE)


POSITION_METRICS = {

    "Attacker": {
        "goals_per90": 0.30,
        "assists_per90": 0.15,
        "shots_on_target_per90": 0.15,
        "key_passes_per90": 0.15,
        "successful_dribbles_per90": 0.15,
        "rating": 0.10
    },

    "Midfielder": {
        "key_passes_per90": 0.20,
        "assists_per90": 0.15,
        "passes_per90": 0.15,
        "successful_dribbles_per90": 0.15,
        "tackles_per90": 0.15,
        "interceptions_per90": 0.10,
        "rating": 0.10
    },

    "Defender": {
        "tackles_per90": 0.25,
        "interceptions_per90": 0.25,
        "passes_per90": 0.20,
        "key_passes_per90": 0.05,
        "successful_dribbles_per90": 0.05,
        "rating": 0.20
    }
}


def percentile_score(value, series):

    series = series.dropna()

    if len(series) == 0:
        return 0

    score = (series <= value).mean() * 100

    return round(score, 1)


def calculate_player_quality(player):

    position = player["position"]

    if position not in POSITION_METRICS:
        return None

    same_position = df[
        df["position"] == position
    ]

    weights = POSITION_METRICS[position]

    total_score = 0

    details = {}

    for metric, weight in weights.items():

        value = player[metric]

        score = percentile_score(
            value,
            same_position[metric]
        )

        details[metric] = score

        total_score += score * weight

    return round(total_score, 1), details


def calculate_squad_upgrade(player, target_team):

    position = player["position"]

    team_players = df[
        (df["team"] == target_team) &
        (df["position"] == position)
    ]

    if team_players.empty:
        return 50

    weights = POSITION_METRICS[position]

    upgrade_score = 0
    total_weight = 0

    for metric, weight in weights.items():

        player_value = player[metric]

        team_average = team_players[metric].mean()

        if team_average == 0:
            metric_score = 50
        else:

            difference = (
                player_value - team_average
            ) / abs(team_average)

            metric_score = 50 + difference * 50

            metric_score = max(
                0,
                min(100, metric_score)
            )

        upgrade_score += metric_score * weight
        total_weight += weight

    return round(
        upgrade_score / total_weight,
        1
    )


def analyze_transfer(player_name, target_team):

    matches = df[
        df["name"].str.lower()
        == player_name.lower()
    ]

    if matches.empty:

        print("Player not found.")
        return

    player = matches.iloc[0]

    if player["team"] == target_team:

        print(
            "Player already belongs to target team."
        )
        return

    quality_result = calculate_player_quality(
        player
    )

    if quality_result is None:

        print(
            "Position not supported yet."
        )
        return

    quality_score, metric_details = quality_result

    upgrade_score = calculate_squad_upgrade(
        player,
        target_team
    )

    rating_score = percentile_score(
        player["rating"],
        df[
            df["position"]
            == player["position"]
        ]["rating"]
    )

    final_score = (
        quality_score * 0.50
        + upgrade_score * 0.35
        + rating_score * 0.15
    )

    final_score = round(final_score, 1)

    print()
    print("==============================")
    print("TRANSFIT AI - ANALYSIS")
    print("==============================")

    print("Player:", player["name"])
    print("Current Club:", player["team"])
    print("Target Club:", target_team)
    print("Position:", player["position"])

    print()
    print("Player Quality:", quality_score)
    print("Squad Upgrade:", upgrade_score)
    print("Performance Rating:", rating_score)

    print()
    print("------------------------------")
    print(
        "STATISTICAL FIT:",
        final_score,
        "/ 100"
    )
    print("------------------------------")

    print()
    print("Metric Percentiles:")

    for metric, score in metric_details.items():

        print(
            metric,
            ":",
            score
        )


# --------------------------------
# TEST
# --------------------------------

print()
print("================================")
print("TRANSFIT AI")
print("Statistical Transfer Analysis")
print("================================")
print()

PLAYER_NAME = input("Enter player name: ").strip()
TARGET_TEAM = input("Enter target club: ").strip()

analyze_transfer(
    PLAYER_NAME,
    TARGET_TEAM
)