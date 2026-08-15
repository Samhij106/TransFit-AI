import pandas as pd


# ============================================================
# CONFIG
# ============================================================

PLAYERS_FILE = "data/processed/player_profiles_2025.csv"
FORMATIONS_FILE = "data/processed/team_formation_profiles_2025.csv"

players_df = pd.read_csv(PLAYERS_FILE)
formations_df = pd.read_csv(FORMATIONS_FILE)


# ============================================================
# FORMATION REQUIREMENTS
#
# format:
# "display role": {
#     "positions": accepted detailed positions,
#     "starters": number required in starting XI
# }
# ============================================================

FORMATION_REQUIREMENTS = {

    "4-3-3": {
        "GK": {
            "positions": ["GK"],
            "starters": 1
        },
        "LB": {
            "positions": ["LB", "LWB"],
            "starters": 1
        },
        "CB": {
            "positions": ["CB"],
            "starters": 2
        },
        "RB": {
            "positions": ["RB", "RWB"],
            "starters": 1
        },
        "CM/CDM": {
            "positions": ["CM", "CDM"],
            "starters": 3
        },
        "LW": {
            "positions": ["LW", "LM"],
            "starters": 1
        },
        "RW": {
            "positions": ["RW", "RM"],
            "starters": 1
        },
        "ST": {
            "positions": ["ST"],
            "starters": 1
        }
    },

    "4-2-3-1": {
        "GK": {
            "positions": ["GK"],
            "starters": 1
        },
        "LB": {
            "positions": ["LB", "LWB"],
            "starters": 1
        },
        "CB": {
            "positions": ["CB"],
            "starters": 2
        },
        "RB": {
            "positions": ["RB", "RWB"],
            "starters": 1
        },
        "CM/CDM": {
            "positions": ["CM", "CDM"],
            "starters": 2
        },
        "CAM": {
            "positions": ["CAM", "CM"],
            "starters": 1
        },
        "LW": {
            "positions": ["LW", "LM"],
            "starters": 1
        },
        "RW": {
            "positions": ["RW", "RM"],
            "starters": 1
        },
        "ST": {
            "positions": ["ST"],
            "starters": 1
        }
    },

    "4-4-2": {
        "GK": {
            "positions": ["GK"],
            "starters": 1
        },
        "LB": {
            "positions": ["LB", "LWB"],
            "starters": 1
        },
        "CB": {
            "positions": ["CB"],
            "starters": 2
        },
        "RB": {
            "positions": ["RB", "RWB"],
            "starters": 1
        },
        "LM": {
            "positions": ["LM", "LW"],
            "starters": 1
        },
        "CM": {
            "positions": ["CM", "CDM"],
            "starters": 2
        },
        "RM": {
            "positions": ["RM", "RW"],
            "starters": 1
        },
        "ST": {
            "positions": ["ST"],
            "starters": 2
        }
    },

    "4-1-4-1": {
        "GK": {
            "positions": ["GK"],
            "starters": 1
        },
        "LB": {
            "positions": ["LB", "LWB"],
            "starters": 1
        },
        "CB": {
            "positions": ["CB"],
            "starters": 2
        },
        "RB": {
            "positions": ["RB", "RWB"],
            "starters": 1
        },
        "CDM": {
            "positions": ["CDM", "CM"],
            "starters": 1
        },
        "LM": {
            "positions": ["LM", "LW"],
            "starters": 1
        },
        "CM": {
            "positions": ["CM", "CAM"],
            "starters": 2
        },
        "RM": {
            "positions": ["RM", "RW"],
            "starters": 1
        },
        "ST": {
            "positions": ["ST"],
            "starters": 1
        }
    },

    "3-4-2-1": {
        "GK": {
            "positions": ["GK"],
            "starters": 1
        },
        "CB": {
            "positions": ["CB"],
            "starters": 3
        },
        "LWB": {
            "positions": ["LWB", "LB", "LM"],
            "starters": 1
        },
        "CM": {
            "positions": ["CM", "CDM"],
            "starters": 2
        },
        "RWB": {
            "positions": ["RWB", "RB", "RM"],
            "starters": 1
        },
        "CAM": {
            "positions": ["CAM", "LW", "RW"],
            "starters": 2
        },
        "ST": {
            "positions": ["ST"],
            "starters": 1
        }
    },

    "3-5-2": {
        "GK": {
            "positions": ["GK"],
            "starters": 1
        },
        "CB": {
            "positions": ["CB"],
            "starters": 3
        },
        "LWB": {
            "positions": ["LWB", "LB", "LM"],
            "starters": 1
        },
        "CM/CDM": {
            "positions": ["CM", "CDM"],
            "starters": 3
        },
        "RWB": {
            "positions": ["RWB", "RB", "RM"],
            "starters": 1
        },
        "ST": {
            "positions": ["ST"],
            "starters": 2
        }
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
        (series <= value).mean() * 100,
        1
    )


def player_quality(player, accepted_positions):

    comparison_pool = players_df[
        players_df["detailed_position"]
        .isin(accepted_positions)
    ]

    rating_score = percentile_score(
        player["rating"],
        comparison_pool["rating"]
    )

    minutes_score = percentile_score(
        player["minutes"],
        comparison_pool["minutes"]
    )

    return round(
        rating_score * 0.75
        + minutes_score * 0.25,
        1
    )


# ============================================================
# ROLE NEED
# ============================================================

def calculate_role_need(
    team,
    role_name,
    role_config
):

    accepted_positions = role_config["positions"]
    starter_count = role_config["starters"]

    team_players = players_df[
        (players_df["team"] == team)
        &
        (
            players_df["detailed_position"]
            .isin(accepted_positions)
        )
    ].copy()

    player_count = len(team_players)

    # We want roughly two players for each starting slot.
    desired_depth = starter_count * 2

    if player_count == 0:

        return {
            "role": role_name,
            "starters_required": starter_count,
            "players_available": 0,
            "quality": 0,
            "depth_need": 100,
            "need_score": 100
        }

    team_players["quality_score"] = (
        team_players.apply(
            lambda player: player_quality(
                player,
                accepted_positions
            ),
            axis=1
        )
    )

    # Only the best players needed for the tactical role
    relevant_players = (
        team_players
        .sort_values(
            "quality_score",
            ascending=False
        )
        .head(desired_depth)
    )

    average_quality = round(
        relevant_players["quality_score"].mean(),
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

    # Quality matters more than raw player count
    need_score = (
        quality_need * 0.75
        + depth_need * 0.25
    )

    need_score = round(
        max(0, min(100, need_score)),
        1
    )

    return {
        "role": role_name,
        "starters_required": starter_count,
        "players_available": player_count,
        "quality": average_quality,
        "depth_need": round(depth_need, 1),
        "need_score": need_score
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

    actual_team_name = team_players.iloc[0]["team"]

    formation_row = formations_df[
        formations_df["team"].str.lower()
        == actual_team_name.lower()
    ]

    if formation_row.empty:
        print("Formation profile not found.")
        return

    formation_row = formation_row.iloc[0]

    primary_formation = formation_row[
        "primary_formation"
    ]

    primary_percentage = formation_row[
        "primary_percentage"
    ]

    secondary_formation = formation_row[
        "secondary_formation"
    ]

    secondary_percentage = formation_row[
        "secondary_percentage"
    ]

    print()
    print("==========================================")
    print("TRANSFIT AI")
    print("FORMATION-AWARE SQUAD NEED")
    print("==========================================")

    print()
    print("Club:", actual_team_name)

    print(
        "Primary Formation:",
        primary_formation,
        f"({primary_percentage}%)"
    )

    if pd.notna(secondary_formation):

        print(
            "Secondary Formation:",
            secondary_formation,
            f"({secondary_percentage}%)"
        )

    if primary_formation not in FORMATION_REQUIREMENTS:

        print()
        print(
            "Primary formation is not "
            "supported yet:",
            primary_formation
        )

        return

    formation_roles = (
        FORMATION_REQUIREMENTS[
            primary_formation
        ]
    )

    results = []

    for role_name, role_config in formation_roles.items():

        result = calculate_role_need(
            actual_team_name,
            role_name,
            role_config
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
        f"{'Need':<10}"
        f"{'Quality':<12}"
        f"{'Players':<10}"
        f"{'Priority'}"
    )

    print("-" * 60)

    for _, row in results_df.iterrows():

        print(
            f"{row['role']:<12}"
            f"{row['need_score']:<10}"
            f"{row['quality']:<12}"
            f"{int(row['players_available']):<10}"
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
            f"- {row['need_score']} "
            f"({need_label(row['need_score'])})"
        )


# ============================================================
# INPUT
# ============================================================

print()
print("==========================================")
print("TRANSFIT AI")
print("Squad Need v2")
print("==========================================")
print()

TEAM_NAME = input(
    "Enter club name: "
).strip()

analyze_team(
    TEAM_NAME
)