import pandas as pd
import numpy as np


INPUT_FILE = "data/processed/player_profiles_2025.csv"
OUTPUT_FILE = "data/processed/player_profiles_season_2025.csv"


PER90_COLUMNS = [
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
]


# =========================================================
# HELPERS
# =========================================================

def weighted_average(group, column):
    if column not in group.columns:
        return np.nan

    values = pd.to_numeric(
        group[column],
        errors="coerce",
    )

    weights = pd.to_numeric(
        group["minutes"],
        errors="coerce",
    ).fillna(0)

    valid = (
        values.notna()
        & (weights > 0)
    )

    if valid.any():
        return (
            values[valid]
            * weights[valid]
        ).sum() / weights[valid].sum()

    if values.notna().any():
        return values.mean()

    return np.nan


def join_unique(series):
    values = []

    for value in series.dropna():
        value = str(value).strip()

        if value and value not in values:
            values.append(value)

    return " | ".join(values)


# =========================================================
# LOAD
# =========================================================

df = pd.read_csv(INPUT_FILE)

df["minutes"] = pd.to_numeric(
    df["minutes"],
    errors="coerce",
).fillna(0)


# =========================================================
# CONSOLIDATE EACH PLAYER
# =========================================================

rows = []

for player_id, group in df.groupby(
    "player_id",
    sort=False,
):
    group = group.copy()

    # Use the longest club stint as the base row for
    # non-performance metadata.
    base_index = group["minutes"].idxmax()
    base = group.loc[base_index].copy()

    total_minutes = group["minutes"].sum()

    # -----------------------------------------------------
    # Season clubs
    # -----------------------------------------------------

    season_teams = join_unique(
        group["team"]
    )

    base["team"] = season_teams
    base["season_teams"] = season_teams
    base["club_stints"] = (
        group["team"]
        .dropna()
        .astype(str)
        .nunique()
    )

    base["minutes"] = total_minutes


    # -----------------------------------------------------
    # Weighted rating
    # -----------------------------------------------------

    if "rating" in group.columns:
        base["rating"] = weighted_average(
            group,
            "rating",
        )


    # -----------------------------------------------------
    # Weighted per-90 statistics
    # -----------------------------------------------------

    for column in PER90_COLUMNS:
        if column in group.columns:
            base[column] = weighted_average(
                group,
                column,
            )


    # -----------------------------------------------------
    # Recalculate shot accuracy from estimated totals
    # -----------------------------------------------------

    if (
        "shots_per90" in group.columns
        and "shots_on_target_per90" in group.columns
    ):
        shots = (
            pd.to_numeric(
                group["shots_per90"],
                errors="coerce",
            ).fillna(0)
            * group["minutes"]
            / 90
        ).sum()

        shots_on_target = (
            pd.to_numeric(
                group["shots_on_target_per90"],
                errors="coerce",
            ).fillna(0)
            * group["minutes"]
            / 90
        ).sum()

        if shots > 0:
            base["shot_accuracy"] = (
                shots_on_target
                / shots
                * 100
            )
        else:
            base["shot_accuracy"] = 0


    # -----------------------------------------------------
    # Recalculate dribble success rate
    # -----------------------------------------------------

    if (
        "dribble_attempts_per90" in group.columns
        and "successful_dribbles_per90"
        in group.columns
    ):
        attempts = (
            pd.to_numeric(
                group["dribble_attempts_per90"],
                errors="coerce",
            ).fillna(0)
            * group["minutes"]
            / 90
        ).sum()

        successful = (
            pd.to_numeric(
                group["successful_dribbles_per90"],
                errors="coerce",
            ).fillna(0)
            * group["minutes"]
            / 90
        ).sum()

        if attempts > 0:
            base["dribble_success_rate"] = (
                successful
                / attempts
                * 100
            )
        else:
            base["dribble_success_rate"] = 0


    rows.append(base)


# =========================================================
# SAVE
# =========================================================

output = pd.DataFrame(rows)

output = output.sort_values(
    "player_id"
).reset_index(drop=True)


# Round numeric values for cleaner CSV
numeric_columns = output.select_dtypes(
    include="number"
).columns

output[numeric_columns] = (
    output[numeric_columns]
    .round(3)
)


output.to_csv(
    OUTPUT_FILE,
    index=False,
)


# =========================================================
# VALIDATION
# =========================================================

print("\nPLAYER PROFILE CONSOLIDATION\n")

print(
    f"Input rows:       {len(df)}"
)

print(
    f"Unique players:   "
    f"{df['player_id'].nunique()}"
)

print(
    f"Output rows:      {len(output)}"
)

print(
    f"Output unique IDs:"
    f" {output['player_id'].nunique()}"
)

print(
    f"Transferred players: "
    f"{(output['club_stints'] > 1).sum()}"
)


print("\nMULTI-CLUB PLAYERS:\n")

print(
    output[
        output["club_stints"] > 1
    ][
        [
            "player_id",
            "name",
            "team",
            "minutes",
            "club_stints",
        ]
    ].to_string(index=False)
)


print(
    f"\nOutput: {OUTPUT_FILE}"
)