import pandas as pd


# ============================================================
# CONFIG
# ============================================================

PLAYERS_FILE = "data/processed/player_profiles_2025.csv"
FORMATIONS_FILE = "data/processed/team_formation_profiles_2025.csv"

players_df = pd.read_csv(PLAYERS_FILE)
formations_df = pd.read_csv(FORMATIONS_FILE)


# ============================================================
# POSITION METRICS
# ============================================================

POSITION_METRICS = {

    "ST": {
        "goals_per90": 0.30,
        "shots_on_target_per90": 0.20,
        "shots_per90": 0.15,
        "assists_per90": 0.10,
        "key_passes_per90": 0.05,
        "rating": 0.20
    },

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
        "successful_dribbles_per90": 0.15,
        "tackles_per90": 0.10,
        "passes_per90": 0.15,
        "rating": 0.25
    },

    "RM": {
        "assists_per90": 0.15,
        "key_passes_per90": 0.20,
        "successful_dribbles_per90": 0.15,
        "tackles_per90": 0.10,
        "passes_per90": 0.15,
        "rating": 0.25
    },

    "CAM": {
        "assists_per90": 0.20,
        "key_passes_per90": 0.25,
        "successful_dribbles_per90": 0.15,
        "goals_per90": 0.10,
        "passes_per90": 0.10,
        "rating": 0.20
    },

    "CM": {
        "passes_per90": 0.20,
        "key_passes_per90": 0.15,
        "assists_per90": 0.10,
        "tackles_per90": 0.15,
        "interceptions_per90": 0.15,
        "successful_dribbles_per90": 0.05,
        "rating": 0.20
    },

    "CDM": {
        "tackles_per90": 0.25,
        "interceptions_per90": 0.25,
        "passes_per90": 0.20,
        "key_passes_per90": 0.05,
        "successful_dribbles_per90": 0.05,
        "rating": 0.20
    },

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

    "CB": {
        "tackles_per90": 0.20,
        "interceptions_per90": 0.25,
        "passes_per90": 0.20,
        "rating": 0.25,
        "key_passes_per90": 0.05,
        "assists_per90": 0.05
    },

    "GK": {
        "rating": 1.00
    }
}


# ============================================================
# FORMATION REQUIREMENTS
# ============================================================

FORMATION_REQUIREMENTS = {

    "4-3-3": {
        "GK": (["GK"], 1),
        "LB": (["LB", "LWB"], 1),
        "CB": (["CB"], 2),
        "RB": (["RB", "RWB"], 1),
        "CM/CDM": (["CM", "CDM"], 3),
        "LW": (["LW", "LM"], 1),
        "RW": (["RW", "RM"], 1),
        "ST": (["ST"], 1)
    },

    "4-2-3-1": {
        "GK": (["GK"], 1),
        "LB": (["LB", "LWB"], 1),
        "CB": (["CB"], 2),
        "RB": (["RB", "RWB"], 1),
        "CM/CDM": (["CM", "CDM"], 2),
        "CAM": (["CAM", "CM"], 1),
        "LW": (["LW", "LM"], 1),
        "RW": (["RW", "RM"], 1),
        "ST": (["ST"], 1)
    },

    "4-4-2": {
        "GK": (["GK"], 1),
        "LB": (["LB", "LWB"], 1),
        "CB": (["CB"], 2),
        "RB": (["RB", "RWB"], 1),
        "LM": (["LM", "LW"], 1),
        "CM": (["CM", "CDM"], 2),
        "RM": (["RM", "RW"], 1),
        "ST": (["ST"], 2)
    },

    "4-1-4-1": {
        "GK": (["GK"], 1),
        "LB": (["LB", "LWB"], 1),
        "CB": (["CB"], 2),
        "RB": (["RB", "RWB"], 1),
        "CDM": (["CDM", "CM"], 1),
        "LM": (["LM", "LW"], 1),
        "CM": (["CM", "CAM"], 2),
        "RM": (["RM", "RW"], 1),
        "ST": (["ST"], 1)
    },

    "3-4-2-1": {
        "GK": (["GK"], 1),
        "CB": (["CB"], 3),
        "LWB": (["LWB", "LB", "LM"], 1),
        "CM": (["CM", "CDM"], 2),
        "RWB": (["RWB", "RB", "RM"], 1),
        "CAM": (["CAM", "LW", "RW"], 2),
        "ST": (["ST"], 1)
    },

    "3-5-2": {
        "GK": (["GK"], 1),
        "CB": (["CB"], 3),
        "LWB": (["LWB", "LB", "LM"], 1),
        "CM/CDM": (["CM", "CDM"], 3),
        "RWB": (["RWB", "RB", "RM"], 1),
        "ST": (["ST"], 2)
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
        return 50.0

    return round(
        (series <= float(value)).mean() * 100,
        1
    )


def calculate_player_quality(player, accepted_positions):

    position = player["detailed_position"]

    if position not in POSITION_METRICS:
        return 50.0

    metrics = POSITION_METRICS[position]

    comparison_pool = players_df[
        players_df["detailed_position"]
        .isin(accepted_positions)
    ]

    total_score = 0
    total_weight = 0

    for metric, weight in metrics.items():

        if metric not in players_df.columns:
            continue

        value = player[metric]

        if pd.isna(value):
            continue

        score = percentile_score(
            value,
            comparison_pool[metric]
        )

        total_score += score * weight
        total_weight += weight

    if total_weight == 0:
        return 50.0

    return round(
        total_score / total_weight,
        1
    )


# ============================================================
# ROLE NEED
# ============================================================

def calculate_role_need(
    team,
    role,
    accepted_positions,
    starters_required
):

    team_players = players_df[
        (players_df["team"] == team)
        &
        (
            players_df["detailed_position"]
            .isin(accepted_positions)
        )
    ].copy()

    player_count = len(team_players)

    desired_depth = starters_required * 2

    if player_count == 0:

        return {
            "role": role,
            "players": 0,
            "quality": 0,
            "depth_need": 100,
            "need_score": 100
        }

    team_players["quality_score"] = (
        team_players.apply(
            lambda player:
            calculate_player_quality(
                player,
                accepted_positions
            ),
            axis=1
        )
    )

    # Best players are most relevant
    best_players = (
        team_players
        .sort_values(
            "quality_score",
            ascending=False
        )
        .head(desired_depth)
    )

    average_quality = round(
        best_players["quality_score"].mean(),
        1
    )

    quality_need = 100 - average_quality

    if player_count >= desired_depth:
        depth_need = 0

    else:

        depth_need = (
            (desired_depth - player_count)
            / desired_depth
            * 100
        )

    # Player quality is more important than quantity
    need_score = (
        quality_need * 0.80
        +
        depth_need * 0.20
    )

    return {
        "role": role,
        "players": player_count,
        "quality": average_quality,
        "depth_need": round(depth_need, 1),
        "need_score": round(
            max(0, min(100, need_score)),
            1
        )
    }


# ============================================================
# LABEL
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
# TEAM ANALYSIS
# ============================================================

def analyze_team(team_name):

    team_players = players_df[
        players_df["team"].str.lower()
        == team_name.lower()
    ]

    if team_players.empty:
        print("Team not found.")
        return

    actual_team = team_players.iloc[0]["team"]

    formation_match = formations_df[
        formations_df["team"].str.lower()
        == actual_team.lower()
    ]

    if formation_match.empty:
        print("Formation not found.")
        return

    formation_data = formation_match.iloc[0]

    primary_formation = formation_data[
        "primary_formation"
    ]

    primary_percentage = formation_data[
        "primary_percentage"
    ]

    print()
    print("==========================================")
    print("TRANSFIT AI")
    print("SQUAD NEED V3")
    print("==========================================")
    print()

    print("Club:", actual_team)

    print(
        "Primary Formation:",
        primary_formation,
        f"({primary_percentage}%)"
    )

    if primary_formation not in FORMATION_REQUIREMENTS:

        print()
        print(
            "Formation currently unsupported:",
            primary_formation
        )

        return

    formation_roles = (
        FORMATION_REQUIREMENTS[
            primary_formation
        ]
    )

    results = []

    for role, config in formation_roles.items():

        accepted_positions = config[0]
        starters_required = config[1]

        result = calculate_role_need(
            actual_team,
            role,
            accepted_positions,
            starters_required
        )

        results.append(result)

    results_df = pd.DataFrame(results)

    results_df = results_df.sort_values(
        "need_score",
        ascending=False
    )

    print()
    print(
        f"{'Role':<12}"
        f"{'Players':<10}"
        f"{'Quality':<12}"
        f"{'Need':<10}"
        f"{'Priority'}"
    )

    print("-" * 60)

    for _, row in results_df.iterrows():

        print(
            f"{row['role']:<12}"
            f"{int(row['players']):<10}"
            f"{row['quality']:<12}"
            f"{row['need_score']:<10}"
            f"{need_label(row['need_score'])}"
        )

    print()
    print("TOP TRANSFER PRIORITIES")
    print("------------------------------------------")

    for rank, (_, row) in enumerate(
        results_df.head(5).iterrows(),
        start=1
    ):

        print(
            f"{rank}. "
            f"{row['role']} "
            f"- Need Score: "
            f"{row['need_score']} "
            f"({need_label(row['need_score'])})"
        )


# ============================================================
# INPUT
# ============================================================

print()
print("==========================================")
print("TRANSFIT AI")
print("Squad Need v3")
print("==========================================")
print()

TEAM_NAME = input(
    "Enter club name: "
).strip()

analyze_team(
    TEAM_NAME
)