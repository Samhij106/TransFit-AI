import pandas as pd


# ============================================================
# CONFIG
# ============================================================

PLAYERS_FILE = "data/processed/player_profiles_2025.csv"
FORMATIONS_FILE = "data/processed/team_formation_profiles_2025.csv"

players_df = pd.read_csv(PLAYERS_FILE)
formations_df = pd.read_csv(FORMATIONS_FILE)


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

players_df["role_group"] = (
    players_df["detailed_position"]
    .map(POSITION_GROUPS)
)


# ============================================================
# POSITION-SPECIFIC METRICS
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
        "passes_per90": 0.15,
        "tackles_per90": 0.10,
        "rating": 0.25
    },

    "RM": {
        "assists_per90": 0.15,
        "key_passes_per90": 0.20,
        "successful_dribbles_per90": 0.15,
        "passes_per90": 0.15,
        "tackles_per90": 0.10,
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

    "4-2-2-2": {
    "GK": (["GK"], 1),

    "LB": (["LB", "LWB"], 1),
    "CB": (["CB"], 2),
    "RB": (["RB", "RWB"], 1),

    "CM/CDM": (["CM", "CDM"], 2),

    "CAM": (
        ["CAM", "LW", "RW", "LM", "RM"],
        2
    ),

    "ST": (["ST"], 2)
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


def find_team(team_name):

    match = players_df[
        players_df["team"].str.lower()
        == team_name.lower()
    ]

    if match.empty:
        return None

    return match.iloc[0]["team"]


# ============================================================
# PLAYER QUALITY
# ============================================================

def calculate_player_quality(player):

    position = player["detailed_position"]

    if position not in POSITION_METRICS:
        return None, {}

    role_group = player["role_group"]

    comparison_pool = players_df[
        players_df["role_group"] == role_group
    ]

    metrics = POSITION_METRICS[position]

    total_score = 0
    total_weight = 0

    details = {}

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

        details[metric] = score

        total_score += score * weight
        total_weight += weight

    if total_weight == 0:
        return 50.0, details

    return (
        round(total_score / total_weight, 1),
        details
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

    target_players = players_df[
        (players_df["team"] == target_team)
        &
        (players_df["role_group"] == role_group)
    ].copy()

    if target_players.empty:
        return 85.0

    candidate_quality, _ = (
        calculate_player_quality(player)
    )

    target_qualities = []

    for _, target_player in target_players.iterrows():

        quality, _ = (
            calculate_player_quality(
                target_player
            )
        )

        if quality is not None:
            target_qualities.append(quality)

    if not target_qualities:
        return 65.0

    # Compare candidate against best relevant players
    target_qualities.sort(
        reverse=True
    )

    top_target_players = target_qualities[:2]

    target_quality = (
        sum(top_target_players)
        / len(top_target_players)
    )

    difference = (
        candidate_quality
        - target_quality
    )

    # 50 = similar level
    # >50 = upgrade
    # <50 = downgrade
    upgrade_score = (
        50 + difference
    )

    return round(
        max(
            0,
            min(100, upgrade_score)
        ),
        1
    )


# ============================================================
# FIND FORMATION ROLE
# ============================================================

def find_best_role(
    detailed_position,
    formation
):

    if formation not in FORMATION_REQUIREMENTS:
        return None

    roles = FORMATION_REQUIREMENTS[
        formation
    ]

    candidates = []

    for role, config in roles.items():

        accepted_positions = config[0]
        starters = config[1]

        if detailed_position not in accepted_positions:
            continue

        # Prefer direct position match
        if role == detailed_position:
            priority = 3

        elif detailed_position in role.split("/"):
            priority = 3

        elif (
            accepted_positions
            and accepted_positions[0]
            == detailed_position
        ):
            priority = 2

        else:
            priority = 1

        candidates.append(
            (
                priority,
                role,
                accepted_positions,
                starters
            )
        )

    if not candidates:
        return None

    candidates.sort(
        reverse=True,
        key=lambda x: x[0]
    )

    _, role, accepted_positions, starters = (
        candidates[0]
    )

    return {
        "role": role,
        "positions": accepted_positions,
        "starters": starters
    }


# ============================================================
# ROLE QUALITY
# ============================================================

def calculate_role_player_quality(
    player,
    accepted_positions
):

    position = player[
        "detailed_position"
    ]

    if position not in POSITION_METRICS:
        return 50.0

    comparison_pool = players_df[
        players_df[
            "detailed_position"
        ].isin(accepted_positions)
    ]

    metrics = POSITION_METRICS[
        position
    ]

    total = 0
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

        total += score * weight
        total_weight += weight

    if total_weight == 0:
        return 50.0

    return round(
        total / total_weight,
        1
    )


# ============================================================
# FORMATION-AWARE ROLE NEED
# ============================================================

def calculate_role_need(
    target_team,
    accepted_positions,
    starters
):

    team_players = players_df[
        (players_df["team"] == target_team)
        &
        (
            players_df[
                "detailed_position"
            ].isin(accepted_positions)
        )
    ].copy()

    desired_depth = starters * 2

    if team_players.empty:
        return 100.0

    qualities = []

    for _, player in team_players.iterrows():

        quality = (
            calculate_role_player_quality(
                player,
                accepted_positions
            )
        )

        qualities.append(quality)

    qualities.sort(
        reverse=True
    )

    relevant = qualities[
        :desired_depth
    ]

    average_quality = (
        sum(relevant)
        / len(relevant)
    )

    quality_need = (
        100 - average_quality
    )

    player_count = len(
        team_players
    )

    if player_count >= desired_depth:
        depth_need = 0

    else:
        depth_need = (
            (desired_depth - player_count)
            / desired_depth
            * 100
        )

    need = (
        quality_need * 0.80
        +
        depth_need * 0.20
    )

    return round(
        max(
            0,
            min(100, need)
        ),
        1
    )


# ============================================================
# FORMATION + SQUAD NEED
# ============================================================

def calculate_tactical_need(
    player,
    target_team
):

    formation_match = formations_df[
        formations_df["team"].str.lower()
        == target_team.lower()
    ]

    if formation_match.empty:
        return 50.0, 50.0, []

    formation_data = (
        formation_match.iloc[0]
    )

    primary = formation_data[
        "primary_formation"
    ]

    primary_pct = float(
        formation_data[
            "primary_percentage"
        ]
    )

    secondary = formation_data[
        "secondary_formation"
    ]

    secondary_pct = formation_data[
        "secondary_percentage"
    ]

    if pd.isna(secondary_pct):
        secondary_pct = 0

    secondary_pct = float(
        secondary_pct
    )

    total_usage = (
        primary_pct
        + secondary_pct
    )

    if total_usage == 0:

        formation_data_list = [
            (primary, 1.0)
        ]

    else:

        formation_data_list = [
            (
                primary,
                primary_pct
                / total_usage
            )
        ]

        if (
            pd.notna(secondary)
            and secondary_pct > 0
        ):

            formation_data_list.append(
                (
                    secondary,
                    secondary_pct
                    / total_usage
                )
            )

    position = player[
        "detailed_position"
    ]

    total_need = 0
    formation_fit = 0

    role_details = []

    for formation, weight in formation_data_list:

        role = find_best_role(
            position,
            formation
        )

        if role is None:

            role_details.append(
                {
                    "formation": formation,
                    "role": None,
                    "weight": weight
                }
            )

            continue

        formation_fit += (
            weight * 100
        )

        role_need = (
            calculate_role_need(
                target_team,
                role["positions"],
                role["starters"]
            )
        )

        total_need += (
            role_need * weight
        )

        role_details.append(
            {
                "formation": formation,
                "role": role["role"],
                "weight": weight,
                "need": role_need
            }
        )

    return (
        round(total_need, 1),
        round(formation_fit, 1),
        role_details
    )


# ============================================================
# POSITION CONFIDENCE
# ============================================================

def calculate_position_fit(player):

    confidence = player[
        "position_confidence"
    ]

    if pd.isna(confidence):
        return 50.0

    return round(
        min(
            100,
            float(confidence)
        ),
        1
    )


# ============================================================
# SCORE LABEL
# ============================================================

def score_label(score):

    if score >= 85:
        return "EXCELLENT FIT"

    if score >= 75:
        return "STRONG FIT"

    if score >= 65:
        return "GOOD FIT"

    if score >= 50:
        return "MODERATE FIT"

    return "LOW FIT"


# ============================================================
# MAIN TRANSFER ANALYSIS
# ============================================================

def analyze_transfer(
    player_name,
    target_team_name
):

    player_matches = players_df[
        players_df["name"]
        .str.lower()
        == player_name.lower()
    ]

    if player_matches.empty:

        print()
        print("Player not found.")
        return

    # If duplicate names exist, take the one
    # with the most minutes.
    player = (
        player_matches
        .sort_values(
            "minutes",
            ascending=False
        )
        .iloc[0]
    )

    target_team = find_team(
        target_team_name
    )

    if target_team is None:

        print()
        print("Target club not found.")
        return

    if (
        player["team"].lower()
        == target_team.lower()
    ):

        print()
        print(
            "Player already plays for "
            "the target club."
        )
        return

    if (
        player[
            "detailed_position"
        ]
        == "GK"
    ):

        print()
        print(
            "Goalkeeper model is not "
            "supported yet."
        )
        return

    # --------------------------------------------------------
    # COMPONENTS
    # --------------------------------------------------------

    player_quality, metrics = (
        calculate_player_quality(
            player
        )
    )

    squad_upgrade = (
        calculate_squad_upgrade(
            player,
            target_team
        )
    )

    squad_need, formation_fit, roles = (
        calculate_tactical_need(
            player,
            target_team
        )
    )

    position_fit = (
        calculate_position_fit(
            player
        )
    )

    # --------------------------------------------------------
    # FINAL TRANSFIT SCORE V1
    # --------------------------------------------------------

    transfit_score = (

        player_quality * 0.35

        + squad_upgrade * 0.25

        + squad_need * 0.20

        + position_fit * 0.10

        + formation_fit * 0.10
    )

    transfit_score = round(
        transfit_score,
        1
    )

    # ========================================================
    # OUTPUT
    # ========================================================

    print()
    print("==========================================")
    print("TRANSFIT AI")
    print("TRANSFER FIT ANALYSIS V1")
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
        target_team
    )

    print(
        "Primary Position:",
        player[
            "detailed_position"
        ]
    )

    print(
        "Secondary Position:",
        player[
            "secondary_position"
        ]
    )

    print()

    print("------------------------------------------")
    print("FIT COMPONENTS")
    print("------------------------------------------")

    print(
        f"Player Quality:       "
        f"{player_quality}/100"
    )

    print(
        f"Squad Upgrade:        "
        f"{squad_upgrade}/100"
    )

    print(
        f"Squad Need:           "
        f"{squad_need}/100"
    )

    print(
        f"Position Fit:         "
        f"{position_fit}/100"
    )

    print(
        f"Formation Fit:        "
        f"{formation_fit}/100"
    )

    print()
    print("==========================================")

    print(
        "TRANSFIT SCORE:",
        transfit_score,
        "/ 100"
    )

    print(
        "VERDICT:",
        score_label(
            transfit_score
        )
    )

    print("==========================================")

    print()
    print("FORMATION ROLE ANALYSIS")
    print("------------------------------------------")

    for role in roles:

        if role["role"] is None:

            print(
                role["formation"],
                "-> Position not used"
            )

        else:

            print(
                role["formation"],
                "->",
                role["role"],
                "| Need:",
                role["need"]
            )

    print()
    print("TOP PLAYER STRENGTHS")
    print("------------------------------------------")

    top_metrics = sorted(
        metrics.items(),
        key=lambda item: item[1],
        reverse=True
    )[:3]

    for metric, score in top_metrics:

        print(
            metric,
            ":",
            score
        )

    print()
    print("WEAKEST METRICS")
    print("------------------------------------------")

    weak_metrics = sorted(
        metrics.items(),
        key=lambda item: item[1]
    )[:3]

    for metric, score in weak_metrics:

        print(
            metric,
            ":",
            score
        )


# ============================================================
# INTERACTIVE MODE
# ============================================================

print()
print("==========================================")
print("TRANSFIT AI")
print("Transfer Fit Engine v1")
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