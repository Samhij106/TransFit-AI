import os
import time
from collections import defaultdict

import pandas as pd
import requests
from dotenv import load_dotenv


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")

HEADERS = {
    "x-apisports-key": API_KEY
}

FIXTURES_URL = "https://v3.football.api-sports.io/fixtures"

LEAGUE_ID = 39
LEAGUE_NAME = "Premier League"
SEASON = 2025

OUTPUT_FILE = (
    "data/processed/"
    "team_tactical_profiles_premier_league_2025.csv"
)

os.makedirs("data/processed", exist_ok=True)


# ============================================================
# HELPERS
# ============================================================

def chunk_list(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def numeric_value(value):

    if value is None:
        return None

    if isinstance(value, str):

        value = value.replace("%", "").strip()

        if value == "":
            return None

    try:
        return float(value)

    except (ValueError, TypeError):
        return None


def percentile_score(value, series):

    clean_series = pd.to_numeric(
        series,
        errors="coerce"
    ).dropna()

    if len(clean_series) == 0:
        return 50.0

    return round(
        (clean_series <= value).mean() * 100,
        1
    )


# ============================================================
# 1. GET COMPLETED FIXTURES
# ============================================================

print()
print("==========================================")
print("TRANSFIT AI")
print("TEAM TACTICAL PROFILE")
print("==========================================")
print()

print("Downloading fixture IDs...")


response = requests.get(
    FIXTURES_URL,
    headers=HEADERS,
    params={
        "league": LEAGUE_ID,
        "season": SEASON,
        "status": "FT-AET-PEN"
    }
)

data = response.json()


if data.get("errors"):

    print(
        "Fixture API Error:",
        data["errors"]
    )

    raise SystemExit


fixtures = data.get("response", [])


fixture_ids = [
    fixture["fixture"]["id"]
    for fixture in fixtures
]


print("Completed fixtures:", len(fixture_ids))


# ============================================================
# 2. STORAGE
# ============================================================

team_matches = defaultdict(list)

team_names = {}


# ============================================================
# 3. DOWNLOAD FULL FIXTURE DATA
# ============================================================

fixture_batches = list(
    chunk_list(
        fixture_ids,
        20
    )
)

print(
    "Fixture batches:",
    len(fixture_batches)
)

print()


for batch_number, fixture_group in enumerate(
    fixture_batches,
    start=1
):

    ids_parameter = "-".join(
        str(fixture_id)
        for fixture_id in fixture_group
    )


    response = requests.get(
        FIXTURES_URL,
        headers=HEADERS,
        params={
            "ids": ids_parameter
        }
    )


    batch_data = response.json()


    if batch_data.get("errors"):

        print(
            f"Batch {batch_number} error:",
            batch_data["errors"]
        )

        continue


    for fixture in batch_data.get(
        "response",
        []
    ):

        fixture_statistics = fixture.get(
            "statistics",
            []
        )


        for team_block in fixture_statistics:

            team = team_block.get(
                "team",
                {}
            )

            team_id = team.get("id")
            team_name = team.get("name")


            if not team_id:
                continue


            team_names[team_id] = team_name


            # ----------------------------------------------
            # Convert statistics list into dictionary
            # ----------------------------------------------

            stats = {}

            for statistic in team_block.get(
                "statistics",
                []
            ):

                stat_type = statistic.get(
                    "type"
                )

                stat_value = numeric_value(
                    statistic.get("value")
                )

                stats[stat_type] = stat_value


            # ----------------------------------------------
            # Extract useful tactical metrics
            # ----------------------------------------------

            match_record = {

                "possession": stats.get(
                    "Ball Possession"
                ),

                "total_shots": stats.get(
                    "Total Shots"
                ),

                "shots_on_target": stats.get(
                    "Shots on Goal"
                ),

                "shots_inside_box": stats.get(
                    "Shots insidebox"
                ),

                "shots_outside_box": stats.get(
                    "Shots outsidebox"
                ),

                "corners": stats.get(
                    "Corner Kicks"
                ),

                "total_passes": stats.get(
                    "Total passes"
                ),

                "accurate_passes": stats.get(
                    "Passes accurate"
                ),

                "pass_accuracy": stats.get(
                    "Passes %"
                ),

                "fouls": stats.get(
                    "Fouls"
                )
            }


            team_matches[
                team_id
            ].append(
                match_record
            )


    print(
        f"Batch "
        f"{batch_number}/"
        f"{len(fixture_batches)} processed"
    )

    time.sleep(0.3)


# ============================================================
# 4. AGGREGATE TEAM DATA
# ============================================================

rows = []


for team_id, matches in team_matches.items():

    match_df = pd.DataFrame(
        matches
    )


    averages = (
        match_df
        .mean(
            numeric_only=True
        )
    )


    avg_shots = averages.get(
        "total_shots",
        0
    )


    avg_passes = averages.get(
        "total_passes",
        0
    )


    avg_target = averages.get(
        "shots_on_target",
        0
    )


    # --------------------------------------------------------
    # DIRECTNESS
    #
    # More shots relative to passes =
    # more direct attacking style
    # --------------------------------------------------------

    if (
        pd.notna(avg_passes)
        and avg_passes > 0
    ):

        shots_per_100_passes = (
            avg_shots
            / avg_passes
            * 100
        )

    else:

        shots_per_100_passes = 0


    # --------------------------------------------------------
    # SHOOTING EFFICIENCY
    # --------------------------------------------------------

    if (
        pd.notna(avg_shots)
        and avg_shots > 0
    ):

        shot_accuracy = (
            avg_target
            / avg_shots
            * 100
        )

    else:

        shot_accuracy = 0


    rows.append({

        "league_id": LEAGUE_ID,
        "league": LEAGUE_NAME,
        "season": SEASON,

        "team_id": team_id,
        "team": team_names[team_id],

        "matches_analyzed": len(
            matches
        ),

        "avg_possession": round(
            averages.get(
                "possession",
                0
            ),
            2
        ),

        "avg_total_shots": round(
            avg_shots,
            2
        ),

        "avg_shots_on_target": round(
            avg_target,
            2
        ),

        "avg_shots_inside_box": round(
            averages.get(
                "shots_inside_box",
                0
            ),
            2
        ),

        "avg_corners": round(
            averages.get(
                "corners",
                0
            ),
            2
        ),

        "avg_total_passes": round(
            avg_passes,
            2
        ),

        "avg_accurate_passes": round(
            averages.get(
                "accurate_passes",
                0
            ),
            2
        ),

        "avg_pass_accuracy": round(
            averages.get(
                "pass_accuracy",
                0
            ),
            2
        ),

        "shots_per_100_passes": round(
            shots_per_100_passes,
            2
        ),

        "shot_accuracy": round(
            shot_accuracy,
            2
        )
    })


# ============================================================
# 5. CREATE DATAFRAME
# ============================================================

df = pd.DataFrame(
    rows
)


# ============================================================
# 6. TACTICAL SCORES
# ============================================================

# ------------------------------------------------------------
# Possession Control
# ------------------------------------------------------------

df["possession_control"] = (
    df["avg_possession"]
    .apply(
        lambda value:
        percentile_score(
            value,
            df["avg_possession"]
        )
    )
)


# ------------------------------------------------------------
# Passing Control
# ------------------------------------------------------------

pass_volume_score = (
    df["avg_total_passes"]
    .apply(
        lambda value:
        percentile_score(
            value,
            df["avg_total_passes"]
        )
    )
)

pass_accuracy_score = (
    df["avg_pass_accuracy"]
    .apply(
        lambda value:
        percentile_score(
            value,
            df["avg_pass_accuracy"]
        )
    )
)


df["passing_control"] = (

    pass_volume_score * 0.45

    +

    pass_accuracy_score * 0.55

).round(1)


# ------------------------------------------------------------
# Chance Creation
# ------------------------------------------------------------

shots_score = (
    df["avg_total_shots"]
    .apply(
        lambda value:
        percentile_score(
            value,
            df["avg_total_shots"]
        )
    )
)

target_score = (
    df["avg_shots_on_target"]
    .apply(
        lambda value:
        percentile_score(
            value,
            df[
                "avg_shots_on_target"
            ]
        )
    )
)

inside_box_score = (
    df["avg_shots_inside_box"]
    .apply(
        lambda value:
        percentile_score(
            value,
            df[
                "avg_shots_inside_box"
            ]
        )
    )
)


df["chance_creation"] = (

    shots_score * 0.35

    +

    target_score * 0.35

    +

    inside_box_score * 0.30

).round(1)


# ------------------------------------------------------------
# Attacking Pressure
# ------------------------------------------------------------

corner_score = (
    df["avg_corners"]
    .apply(
        lambda value:
        percentile_score(
            value,
            df["avg_corners"]
        )
    )
)


df["attacking_pressure"] = (

    shots_score * 0.45

    +

    corner_score * 0.25

    +

    df[
        "possession_control"
    ] * 0.30

).round(1)


# ------------------------------------------------------------
# Directness
# ------------------------------------------------------------

df["directness"] = (
    df[
        "shots_per_100_passes"
    ]
    .apply(
        lambda value:
        percentile_score(
            value,
            df[
                "shots_per_100_passes"
            ]
        )
    )
)


# ------------------------------------------------------------
# Shooting Efficiency
# ------------------------------------------------------------

df["shooting_efficiency"] = (
    df["shot_accuracy"]
    .apply(
        lambda value:
        percentile_score(
            value,
            df["shot_accuracy"]
        )
    )
)


# ============================================================
# 7. EXPORT
# ============================================================

df = df.sort_values(
    by="team"
)


df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 8. SUMMARY
# ============================================================

print()
print("==========================================")
print("TACTICAL PROFILES READY")
print("==========================================")

print(
    "Teams analyzed:",
    len(df)
)

print()


display_columns = [

    "team",

    "possession_control",

    "passing_control",

    "chance_creation",

    "attacking_pressure",

    "directness",

    "shooting_efficiency"
]


print(
    df[
        display_columns
    ].to_string(
        index=False
    )
)


print()
print(
    "Output:",
    OUTPUT_FILE
)
