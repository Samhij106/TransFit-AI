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
# DESIRED SQUAD DEPTH
# ============================================================

DESIRED_DEPTH = {
    "GK": 2,

    "CB": 4,

    "LB": 2,
    "RB": 2,
    "LWB": 2,
    "RWB": 2,

    "CDM": 2,
    "CM": 3,
    "CAM": 2,

    "LW": 2,
    "RW": 2,
    "LM": 2,
    "RM": 2,

    "ST": 2
}


# ============================================================
# PLAYER QUALITY
# ============================================================

def percentile_score(value, series):

    series = pd.to_numeric(
        series,
        errors="coerce"
    ).dropna()

    if len(series) == 0:
        return 50.0

    return round(
        (series <= value).mean() * 100,
        1
    )


def calculate_player_quality(player):

    position = player["detailed_position"]
    role_group = player["role_group"]

    comparison_pool = df[
        df["role_group"] == role_group
    ]

    # Simple quality base for squad-need calculation
    metrics = [
        "rating",
        "minutes"
    ]

    scores = []

    for metric in metrics:

        score = percentile_score(
            player[metric],
            comparison_pool[metric]
        )

        scores.append(score)

    return round(
        sum(scores) / len(scores),
        1
    )


# ============================================================
# POSITION NEED
# ============================================================

def calculate_position_need(team, position):

    team_position_players = df[
        (df["team"] == team)
        &
        (df["detailed_position"] == position)
    ].copy()

    desired_depth = DESIRED_DEPTH.get(
        position,
        2
    )

    player_count = len(
        team_position_players
    )

    # --------------------------------------------------------
    # No player in position
    # --------------------------------------------------------

    if player_count == 0:

        return {
            "position": position,
            "players": 0,
            "quality": 0,
            "depth_score": 100,
            "need_score": 100
        }

    # --------------------------------------------------------
    # Calculate player quality
    # --------------------------------------------------------

    team_position_players[
        "quality_score"
    ] = team_position_players.apply(
        calculate_player_quality,
        axis=1
    )

    # Best players matter most
    top_players = (
        team_position_players
        .sort_values(
            "quality_score",
            ascending=False
        )
        .head(desired_depth)
    )

    average_quality = round(
        top_players["quality_score"]
        .mean(),
        1
    )

    # --------------------------------------------------------
    # Quality need
    # --------------------------------------------------------

    quality_need = (
        100 - average_quality
    )

    # --------------------------------------------------------
    # Depth need
    # --------------------------------------------------------

    if player_count >= desired_depth:

        depth_need = 0

    else:

        missing_players = (
            desired_depth - player_count
        )

        depth_need = (
            missing_players
            / desired_depth
            * 100
        )

    # --------------------------------------------------------
    # Final squad need
    # --------------------------------------------------------

    need_score = (
        quality_need * 0.70
        +
        depth_need * 0.30
    )

    need_score = round(
        min(100, need_score),
        1
    )

    return {
        "position": position,
        "players": player_count,
        "quality": average_quality,
        "depth_score": round(depth_need, 1),
        "need_score": need_score
    }


# ============================================================
# NEED LABEL
# ============================================================

def need_label(score):

    if score >= 75:
        return "VERY HIGH"

    if score >= 60:
        return "HIGH"

    if score >= 40:
        return "MEDIUM"

    if score >= 20:
        return "LOW"

    return "VERY LOW"


# ============================================================
# ANALYZE TEAM
# ============================================================

def analyze_team_needs(team_name):

    team_matches = df[
        df["team"].str.lower()
        == team_name.lower()
    ]

    if team_matches.empty:

        print()
        print("Team not found.")
        return

    actual_team_name = (
        team_matches.iloc[0]["team"]
    )

    results = []

    for position in DESIRED_DEPTH:

        result = calculate_position_need(
            actual_team_name,
            position
        )

        results.append(result)

    results_df = pd.DataFrame(results)

    results_df = results_df.sort_values(
        "need_score",
        ascending=False
    )


    print()
    print("==========================================")
    print("TRANSFIT AI")
    print("SQUAD NEED ANALYSIS")
    print("==========================================")

    print()
    print("Club:", actual_team_name)

    print()
    print(
        f"{'Position':<10}"
        f"{'Players':<10}"
        f"{'Quality':<12}"
        f"{'Need':<10}"
        f"{'Priority'}"
    )

    print("-" * 55)

    for _, row in results_df.iterrows():

        print(
            f"{row['position']:<10}"
            f"{int(row['players']):<10}"
            f"{row['quality']:<12}"
            f"{row['need_score']:<10}"
            f"{need_label(row['need_score'])}"
        )

    print()

    print("TOP TRANSFER PRIORITIES")
    print("------------------------------------------")

    top_needs = results_df.head(5)

    for rank, (_, row) in enumerate(
        top_needs.iterrows(),
        start=1
    ):

        print(
            f"{rank}. {row['position']} "
            f"- Need Score: {row['need_score']} "
            f"({need_label(row['need_score'])})"
        )


# ============================================================
# USER INPUT
# ============================================================

print()
print("==========================================")
print("TRANSFIT AI")
print("Squad Need Prototype")
print("==========================================")
print()

TEAM_NAME = input(
    "Enter club name: "
).strip()

analyze_team_needs(
    TEAM_NAME
)