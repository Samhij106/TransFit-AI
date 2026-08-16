import pandas as pd
import numpy as np


INPUT_FILE = "data/processed/player_profiles_season_2025.csv"
OUTPUT_FILE = "data/processed/player_tactical_profiles_2025.csv"


# ---------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------

df = pd.read_csv(INPUT_FILE)


# ---------------------------------------------------------
# 2. Position groups
# ---------------------------------------------------------

def get_position_group(row):
    pos = str(row.get("primary_position", "")).upper().strip()
    detailed = str(row.get("detailed_position", "")).upper().strip()

    combined = f"{pos} {detailed}"

    # Goalkeeper
    if any(x in combined for x in ["GK", "GOALKEEPER"]):
        return "GK"

    # Centre backs
    if any(x in combined for x in ["CB", "CENTRE-BACK", "CENTER-BACK"]):
        return "CB"

    # Full backs / Wing backs
    if any(x in combined for x in [
        "LB", "RB", "LWB", "RWB",
        "LEFT-BACK", "RIGHT-BACK",
        "WING-BACK"
    ]):
        return "FB"

    # Defensive midfield
    if any(x in combined for x in ["CDM", "DM", "DEFENSIVE MID"]):
        return "DM"

    # Central midfield
    if any(x in combined for x in ["CM", "CENTRAL MID"]):
        return "CM"

    # Attacking midfield
    if any(x in combined for x in ["CAM", "AM", "ATTACKING MID"]):
        return "AM"

    # Wide players
    if any(x in combined for x in [
        "LW", "RW", "LM", "RM",
        "LEFT WING", "RIGHT WING",
        "WINGER"
    ]):
        return "W"

    # Strikers
    if any(x in combined for x in [
        "ST", "CF", "STRIKER",
        "CENTRE-FORWARD", "CENTER-FORWARD",
        "FORWARD"
    ]):
        return "FW"

    return "OTHER"


df["position_group"] = df.apply(get_position_group, axis=1)


# ---------------------------------------------------------
# 3. Metrics used by tactical model
# ---------------------------------------------------------

metrics = [
    "goals_per90",
    "assists_per90",
    "shots_per90",
    "shots_on_target_per90",
    "passes_per90",
    "key_passes_per90",
    "tackles_per90",
    "interceptions_per90",
    "dribble_attempts_per90",
    "successful_dribbles_per90",
    "shot_accuracy",
    "dribble_success_rate",
    "rating",
]


for col in metrics:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)


# ---------------------------------------------------------
# 4. Percentile scores by position group
# ---------------------------------------------------------

def percentile_by_position(data, column):
    result = pd.Series(index=data.index, dtype=float)

    for group, indexes in data.groupby("position_group").groups.items():
        values = data.loc[indexes, column]

        # If group is too small, use entire dataset instead
        if len(values) < 5:
            result.loc[indexes] = (
                data[column].rank(pct=True).loc[indexes] * 100
            )
        else:
            result.loc[indexes] = (
                values.rank(pct=True) * 100
            )

    return result


for metric in metrics:
    df[f"{metric}_pct"] = percentile_by_position(df, metric)


# ---------------------------------------------------------
# 5. Tactical dimensions
# ---------------------------------------------------------

# Ability to participate in controlled possession
df["possession_control"] = (
    0.55 * df["passes_per90_pct"]
    + 0.20 * df["dribble_success_rate_pct"]
    + 0.15 * df["successful_dribbles_per90_pct"]
    + 0.10 * df["rating_pct"]
)


# Ability to contribute through passing
df["passing_control"] = (
    0.60 * df["passes_per90_pct"]
    + 0.30 * df["key_passes_per90_pct"]
    + 0.10 * df["assists_per90_pct"]
)


# Ability to create chances
df["chance_creation"] = (
    0.45 * df["key_passes_per90_pct"]
    + 0.25 * df["assists_per90_pct"]
    + 0.20 * df["successful_dribbles_per90_pct"]
    + 0.10 * df["rating_pct"]
)


# Ability to apply attacking pressure
df["attacking_pressure"] = (
    0.35 * df["shots_per90_pct"]
    + 0.25 * df["shots_on_target_per90_pct"]
    + 0.20 * df["goals_per90_pct"]
    + 0.20 * df["successful_dribbles_per90_pct"]
)


# Direct attacking behaviour
df["directness"] = (
    0.40 * df["dribble_attempts_per90_pct"]
    + 0.35 * df["shots_per90_pct"]
    + 0.25 * df["key_passes_per90_pct"]
)


# Finishing / shooting efficiency
df["shooting_efficiency"] = (
    0.45 * df["shot_accuracy_pct"]
    + 0.35 * df["goals_per90_pct"]
    + 0.20 * df["shots_on_target_per90_pct"]
)


# ---------------------------------------------------------
# 6. Round tactical scores
# ---------------------------------------------------------

tactical_columns = [
    "possession_control",
    "passing_control",
    "chance_creation",
    "attacking_pressure",
    "directness",
    "shooting_efficiency",
]

df[tactical_columns] = df[tactical_columns].clip(0, 100).round(1)


# ---------------------------------------------------------
# 7. Output columns
# ---------------------------------------------------------

output_columns = [
    "player_id",
    "name",
    "team",
    "age",
    "nationality",
    "photo",
    "primary_position",
    "detailed_position",
    "position_group",
    "position_confidence",
    "minutes",
    "rating",
    *tactical_columns,
]


output = df[output_columns].copy()


# Goalkeeper tactical model will be handled separately later
outfield_mask = output["position_group"] != "GK"

print("\nPLAYER TACTICAL PROFILES\n")

print(
    output.loc[outfield_mask, [
        "name",
        "team",
        "position_group",
        *tactical_columns
    ]]
    .head(30)
    .to_string(index=False)
)


# ---------------------------------------------------------
# 8. Save
# ---------------------------------------------------------

output.to_csv(OUTPUT_FILE, index=False)

print(f"\nOutput: {OUTPUT_FILE}")