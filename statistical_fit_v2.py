import pandas as pd


# ============================================================
# CONFIG
# ============================================================

DATA_FILE = "data/processed/player_profiles_2025.csv"

df = pd.read_csv(DATA_FILE)


# ============================================================
# ROLE GROUPS
# ============================================================

POSITION_GROUPS = {

    "ST": "Striker",

    "LW": "Winger",
    "RW": "Winger",
    "LM": "Winger",
    "RM": "Winger",

    "CAM": "Attacking Midfielder",

    "CM": "Central Midfielder",

    "CDM": "Defensive Midfielder",

    "LB": "Fullback",
    "RB": "Fullback",
    "LWB": "Fullback",
    "RWB": "Fullback",

    "CB": "Centre Back",

    "GK": "Goalkeeper"
}


df["role_group"] = (
    df["detailed_position"]
    .map(POSITION_GROUPS)
)


# ============================================================
# POSITION-SPECIFIC METRIC WEIGHTS
# ============================================================

POSITION_METRICS = {

    # --------------------------------------------------------
    # STRIKER
    # --------------------------------------------------------

    "ST": {
        "goals_per90": 0.30,
        "shots_on_target_per90": 0.20,
        "shots_per90": 0.15,
        "assists_per90": 0.10,
        "key_passes_per90": 0.05,
        "rating": 0.20
    },

    # --------------------------------------------------------
    # WINGERS
    # --------------------------------------------------------

    "LW": {
        "goals_per90": 0.20,
        "assists_per90": 0.15,
        "key_passes_per90": 0.15,
        "successful_dribbles_per90": 0.20,
        "shots_on_target_per90": 0.10,
        "rating": 0.20
    },

    "RW": {
        "goals_per90": 0.20,
        "assists_per90": 0.15,
        "key_passes_per90": 0.15,
        "successful_dribbles_per90": 0.20,
        "shots_on_target_per90": 0.10,
        "rating": 0.20
    },

    "LM": {
        "assists_per90": 0.15,
        "key_passes_per90": 0.20,
        "successful_dribbles_per90": 0.20,
        "goals_per90": 0.10,
        "tackles_per90": 0.10,
        "rating": 0.25
    },

    "RM": {
        "assists_per90": 0.15,
        "key_passes_per90": 0.20,
        "successful_dribbles_per90": 0.20,
        "goals_per90": 0.10,
        "tackles_per90": 0.10,
        "rating": 0.25
    },

    # --------------------------------------------------------
    # ATTACKING MIDFIELDER
    # --------------------------------------------------------

    "CAM": {
        "assists_per90": 0.20,
        "key_passes_per90": 0.25,
        "successful_dribbles_per90": 0.15,
        "goals_per90": 0.10,
        "passes_per90": 0.10,
        "rating": 0.20
    },

    # --------------------------------------------------------
    # CENTRAL MIDFIELDER
    # --------------------------------------------------------

    "CM": {
        "passes_per90": 0.20,
        "key_passes_per90": 0.15,
        "assists_per90": 0.10,
        "tackles_per90": 0.15,
        "interceptions_per90": 0.15,
        "successful_dribbles_per90": 0.05,
        "rating": 0.20
    },

    # --------------------------------------------------------
    # DEFENSIVE MIDFIELDER
    # --------------------------------------------------------

    "CDM": {
        "tackles_per90": 0.25,
        "interceptions_per90": 0.25,
        "passes_per90": 0.20,
        "key_passes_per90": 0.05,
        "successful_dribbles_per90": 0.05,
        "rating": 0.20
    },

    # --------------------------------------------------------
    # FULLBACKS
    # --------------------------------------------------------

    "LB": {
        "tackles_per90": 0.20,
        "interceptions_per90": 0.15,
        "passes_per90": 0.15,
        "key_passes_per90": 0.15,
        "successful_dribbles_per90": 0.15,
        "assists_per90": 0.05,
        "rating": 0.15
    },

    "RB": {
        "tackles_per90": 0.20,
        "interceptions_per90": 0.15,
        "passes_per90": 0.15,
        "key_passes_per90": 0.15,
        "successful_dribbles_per90": 0.15,
        "assists_per90": 0.05,
        "rating": 0.15
    },

    "LWB": {
        "tackles_per90": 0.15,
        "interceptions_per90": 0.10,
        "passes_per90": 0.10,
        "key_passes_per90": 0.20,
        "successful_dribbles_per90": 0.20,
        "assists_per90": 0.10,
        "rating": 0.15
    },

    "RWB": {
        "tackles_per90": 0.15,
        "interceptions_per90": 0.10,
        "passes_per90": 0.10,
        "key_passes_per90": 0.20,
        "successful_dribbles_per90": 0.20,
        "assists_per90": 0.10,
        "rating": 0.15
    },

    # --------------------------------------------------------
    # CENTRE BACK
    # --------------------------------------------------------

    "CB": {
        "tackles_per90": 0.20,
        "interceptions_per90": 0.25,
        "passes_per90": 0.20,
        "rating": 0.25,
        "key_passes_per90": 0.05,
        "assists_per90": 0.05
    }
}


# ============================================================
# HELPERS
# ============================================================

def percentile_score(value, series):

    series = pd.to_numeric(
        series,
        errors="coerce"
    ).dropna()

    if len(series) == 0:
        return 0

    value = float(value)

    score = (
        series <= value
    ).mean() * 100

    return round(score, 1)


def get_comparison_pool(player):

    role_group = player["role_group"]

    return df[
        df["role_group"] == role_group
    ]


# ============================================================
# PLAYER QUALITY
# ============================================================

def calculate_player_quality(player):

    position = player["detailed_position"]

    if position not in POSITION_METRICS:
        return None

    comparison_pool = get_comparison_pool(player)

    weights = POSITION_METRICS[position]

    total_score = 0
    metric_details = {}

    for metric, weight in weights.items():

        value = player[metric]

        score = percentile_score(
            value,
            comparison_pool[metric]
        )

        metric_details[metric] = score

        total_score += (
            score * weight
        )

    return (
        round(total_score, 1),
        metric_details
    )


# ============================================================
# SQUAD UPGRADE
# ============================================================

def calculate_squad_upgrade(
    player,
    target_team
):

    position = player["detailed_position"]
    role_group = player["role_group"]

    weights = POSITION_METRICS[position]

    target_players = df[
        (df["team"] == target_team)
        &
        (df["role_group"] == role_group)
    ]

    if target_players.empty:
        return 65.0

    total_score = 0
    total_weight = 0

    for metric, weight in weights.items():

        player_value = player[metric]

        target_average = (
            target_players[metric]
            .mean()
        )

        if pd.isna(target_average):
            continue

        comparison_values = pd.concat(
            [
                target_players[metric],
                pd.Series([player_value])
            ]
        )

        metric_score = percentile_score(
            player_value,
            comparison_values
        )

        total_score += (
            metric_score * weight
        )

        total_weight += weight

    if total_weight == 0:
        return 50.0

    return round(
        total_score / total_weight,
        1
    )


# ============================================================
# POSITION CONFIDENCE
# ============================================================

def calculate_position_score(player):

    confidence = player.get(
        "position_confidence",
        0
    )

    if pd.isna(confidence):
        return 50.0

    return round(
        min(float(confidence), 100),
        1
    )


# ============================================================
# TRANSFER ANALYSIS
# ============================================================

def analyze_transfer(
    player_name,
    target_team
):

    matches = df[
        df["name"]
        .str.lower()
        == player_name.lower()
    ]

    if matches.empty:

        print()
        print("Player not found.")
        return


    player = matches.iloc[0]


    if player["team"].lower() == target_team.lower():

        print()
        print(
            "Player already belongs "
            "to the target club."
        )
        return


    # Find exact target team spelling
    target_match = df[
        df["team"]
        .str.lower()
        == target_team.lower()
    ]

    if target_match.empty:

        print()
        print("Target club not found.")
        return


    target_team_name = (
        target_match.iloc[0]["team"]
    )


    quality_result = (
        calculate_player_quality(player)
    )


    if quality_result is None:

        print()
        print(
            "This position is not "
            "supported yet."
        )
        return


    quality_score, metric_details = (
        quality_result
    )


    upgrade_score = (
        calculate_squad_upgrade(
            player,
            target_team_name
        )
    )


    position_score = (
        calculate_position_score(
            player
        )
    )


    # --------------------------------------------------------
    # Statistical Fit v2
    # --------------------------------------------------------

    final_score = (
        quality_score * 0.55
        +
        upgrade_score * 0.35
        +
        position_score * 0.10
    )

    final_score = round(
        final_score,
        1
    )


    # ========================================================
    # OUTPUT
    # ========================================================

    print()
    print("==========================================")
    print("TRANSFIT AI")
    print("STATISTICAL FIT V2")
    print("==========================================")

    print()
    print(
        "Player:",
        player["name"]
    )

    print(
        "Current Club:",
        player["team"]
    )

    print(
        "Target Club:",
        target_team_name
    )

    print(
        "Position:",
        player["detailed_position"]
    )

    print(
        "Secondary Position:",
        player["secondary_position"]
    )

    print(
        "Role:",
        player["role_group"]
    )


    print()
    print("------------------------------------------")

    print(
        "Player Quality:",
        quality_score
    )

    print(
        "Squad Upgrade:",
        upgrade_score
    )

    print(
        "Position Confidence:",
        position_score
    )


    print()
    print("==========================================")

    print(
        "STATISTICAL FIT:",
        final_score,
        "/ 100"
    )

    print("==========================================")


    print()
    print("Metric Percentiles:")
    print("------------------------------------------")


    sorted_metrics = sorted(
        metric_details.items(),
        key=lambda item: item[1],
        reverse=True
    )


    for metric, score in sorted_metrics:

        print(
            f"{metric:<32}"
            f"{score}"
        )


# ============================================================
# INTERACTIVE INPUT
# ============================================================

print()
print("==========================================")
print("TRANSFIT AI")
print("Transfer Analysis Prototype")
print("==========================================")
print()

PLAYER_NAME = input(
    "Enter player name: "
).strip()

TARGET_TEAM = input(
    "Enter target club: "
).strip()


analyze_transfer(
    PLAYER_NAME,
    TARGET_TEAM
)