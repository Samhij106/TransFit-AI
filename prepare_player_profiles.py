import os
import pandas as pd

INPUT_FILE = "data/raw/premier_league_players_2024.csv"
OUTPUT_FILE = "data/processed/player_profiles_2024.csv"

MIN_MINUTES = 300

os.makedirs("data/processed", exist_ok=True)

# --------------------------------------------------
# Load dataset
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

print("Raw players:", len(df))

# --------------------------------------------------
# Clean data
# --------------------------------------------------

# Keep players with meaningful playing time
df = df[df["minutes"] >= MIN_MINUTES].copy()

# Columns where missing values should become 0
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
    df[column] = df[column].fillna(0)

# Rating can remain missing, but remove players without rating
df = df[df["rating"].notna()].copy()

# --------------------------------------------------
# Calculate per-90 metrics
# --------------------------------------------------

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
        df[column] / df["minutes"] * 90
    ).round(3)

# --------------------------------------------------
# Additional useful metrics
# --------------------------------------------------

df["shot_accuracy"] = (
    df["shots_on_target"] / df["shots"] * 100
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

# --------------------------------------------------
# Position groups
# --------------------------------------------------

valid_positions = [
    "Goalkeeper",
    "Defender",
    "Midfielder",
    "Attacker"
]

df = df[df["position"].isin(valid_positions)].copy()

# --------------------------------------------------
# Remove duplicates
# --------------------------------------------------

df = df.drop_duplicates(
    subset=[
        "player_id",
        "team_id",
        "season"
    ]
)

# --------------------------------------------------
# Sort
# --------------------------------------------------

df = df.sort_values(
    by=["position", "rating"],
    ascending=[True, False]
)

# --------------------------------------------------
# Export
# --------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("==============================")
print("PLAYER PROFILES READY")
print("==============================")
print("Players after cleaning:", len(df))
print()

print("Players by position:")
print(df["position"].value_counts())

print()
print("Output:", OUTPUT_FILE)