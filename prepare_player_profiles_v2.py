import os
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

STATS_FILE = "data/raw/big_five_players_2025.csv"
POSITIONS_FILE = (
    "data/processed/"
    "player_positions_big_five_2025.csv"
)

OUTPUT_FILE = "data/processed/player_profiles_2025.csv"

MIN_MINUTES = 300

os.makedirs("data/processed", exist_ok=True)


# ============================================================
# 1. LOAD DATA
# ============================================================

stats_df = pd.read_csv(STATS_FILE)
positions_df = pd.read_csv(POSITIONS_FILE)

print("Player statistics:", len(stats_df))
print("Players with inferred positions:", len(positions_df))


# ============================================================
# 2. MERGE STATISTICS + DETAILED POSITIONS
# ============================================================

df = stats_df.merge(
    positions_df[
        [
            "player_id",
            "primary_position",
            "primary_starts",
            "secondary_position",
            "secondary_starts",
            "total_starts",
            "position_confidence",
            "unknown_starts",
            "position_history",
            "position_source",
            "broad_position",
        ]
    ],
    on="player_id",
    how="left"
)


# ============================================================
# 3. FILTER PLAYING TIME
# ============================================================

df = df[
    df["minutes"] >= MIN_MINUTES
].copy()


# ============================================================
# 4. CLEAN NUMERIC DATA
# ============================================================

numeric_columns = [
    "goals",
    "assists",
    "shots",
    "shots_on_target",
    "passes",
    "key_passes",
    "tackles",
    "interceptions",
    "dribble_attempts",
    "successful_dribbles"
]

for column in numeric_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    ).fillna(0)


df["rating"] = pd.to_numeric(
    df["rating"],
    errors="coerce"
)

df = df[
    df["rating"].notna()
].copy()


# ============================================================
# 5. FALLBACK POSITION
# ============================================================

fallback_positions = {
    "Goalkeeper": "GK",
    "Defender": "DEF",
    "Midfielder": "MID",
    "Attacker": "ATT"
}


df["detailed_position"] = df["primary_position"]


missing_position = (
    df["detailed_position"].isna()
    | (df["detailed_position"] == "Unknown")
)


df.loc[
    missing_position,
    "detailed_position"
] = (
    df.loc[
        missing_position,
        "position"
    ]
    .map(fallback_positions)
    .fillna("Unknown")
)


# ============================================================
# 6. PER-90 METRICS
# ============================================================

per90_columns = [
    "goals",
    "assists",
    "shots",
    "shots_on_target",
    "passes",
    "key_passes",
    "tackles",
    "interceptions",
    "dribble_attempts",
    "successful_dribbles"
]


for column in per90_columns:

    df[f"{column}_per90"] = (
        df[column]
        / df["minutes"]
        * 90
    ).round(3)


# ============================================================
# 7. EXTRA METRICS
# ============================================================

df["shot_accuracy"] = (
    df["shots_on_target"]
    / df["shots"]
    * 100
).where(
    df["shots"] > 0,
    0
).round(1)


df["dribble_success_rate"] = (
    df["successful_dribbles"]
    / df["dribble_attempts"]
    * 100
).where(
    df["dribble_attempts"] > 0,
    0
).round(1)


# ============================================================
# 8. REMOVE DUPLICATES
# ============================================================

df = df.drop_duplicates(
    subset=[
        "player_id",
        "team_id",
        "season"
    ]
)


# ============================================================
# 9. SORT
# ============================================================

df = df.sort_values(
    by=[
        "detailed_position",
        "rating"
    ],
    ascending=[
        True,
        False
    ]
)


# ============================================================
# 10. EXPORT
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print()
print("==========================================")
print("TRANSFIT AI - PLAYER PROFILES V2")
print("==========================================")

print("Players after cleaning:", len(df))
print("Teams:", df["team"].nunique())

print()
print("Detailed positions:")
print(
    df["detailed_position"]
    .value_counts()
)

print()
print(
    "Players without specific position:",
    df["detailed_position"]
    .isin(["DEF", "MID", "ATT", "Unknown"])
    .sum()
)

print()
print("Output:", OUTPUT_FILE)
