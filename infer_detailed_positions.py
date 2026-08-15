import os
import time
from collections import defaultdict, Counter

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

OUTPUT_FILE = "data/processed/player_positions_2025.csv"

os.makedirs("data/processed", exist_ok=True)


# ============================================================
# POSITION MAPS
# ============================================================

POSITION_MAPS = {

    "4-2-3-1": {
        "1:1": "GK",

        "2:1": "LB",
        "2:2": "CB",
        "2:3": "CB",
        "2:4": "RB",

        "3:1": "CDM",
        "3:2": "CDM",

        "4:1": "LW",
        "4:2": "CAM",
        "4:3": "RW",

        "5:1": "ST"
    },

    "4-3-3": {
        "1:1": "GK",

        "2:1": "LB",
        "2:2": "CB",
        "2:3": "CB",
        "2:4": "RB",

        "3:1": "CM",
        "3:2": "CM",
        "3:3": "CM",

        "4:1": "LW",
        "4:2": "ST",
        "4:3": "RW"
    },

    "4-3-2-1": {
        "1:1": "GK",

        "2:1": "LB",
        "2:2": "CB",
        "2:3": "CB",
        "2:4": "RB",

        "3:1": "CM",
        "3:2": "CM",
        "3:3": "CM",

        "4:1": "CAM",
        "4:2": "CAM",

        "5:1": "ST"
    },

    "4-1-4-1": {
        "1:1": "GK",

        "2:1": "LB",
        "2:2": "CB",
        "2:3": "CB",
        "2:4": "RB",

        "3:1": "CDM",

        "4:1": "LM",
        "4:2": "CM",
        "4:3": "CM",
        "4:4": "RM",

        "5:1": "ST"
    },

    "4-4-2": {
        "1:1": "GK",

        "2:1": "LB",
        "2:2": "CB",
        "2:3": "CB",
        "2:4": "RB",

        "3:1": "LM",
        "3:2": "CM",
        "3:3": "CM",
        "3:4": "RM",

        "4:1": "ST",
        "4:2": "ST"
    },

    "4-2-2-2": {
        "1:1": "GK",

        "2:1": "LB",
        "2:2": "CB",
        "2:3": "CB",
        "2:4": "RB",

        "3:1": "CDM",
        "3:2": "CDM",

        "4:1": "CAM",
        "4:2": "CAM",

        "5:1": "ST",
        "5:2": "ST"
    },

    "3-4-2-1": {
        "1:1": "GK",

        "2:1": "CB",
        "2:2": "CB",
        "2:3": "CB",

        "3:1": "LWB",
        "3:2": "CM",
        "3:3": "CM",
        "3:4": "RWB",

        "4:1": "CAM",
        "4:2": "CAM",

        "5:1": "ST"
    },

    "3-4-3": {
        "1:1": "GK",

        "2:1": "CB",
        "2:2": "CB",
        "2:3": "CB",

        "3:1": "LWB",
        "3:2": "CM",
        "3:3": "CM",
        "3:4": "RWB",

        "4:1": "LW",
        "4:2": "ST",
        "4:3": "RW"
    },

    "3-5-2": {
        "1:1": "GK",

        "2:1": "CB",
        "2:2": "CB",
        "2:3": "CB",

        "3:1": "LWB",
        "3:2": "CM",
        "3:3": "CDM",
        "3:4": "CM",
        "3:5": "RWB",

        "4:1": "ST",
        "4:2": "ST"
    },

    "3-4-1-2": {
        "1:1": "GK",

        "2:1": "CB",
        "2:2": "CB",
        "2:3": "CB",

        "3:1": "LWB",
        "3:2": "CM",
        "3:3": "CM",
        "3:4": "RWB",

        "4:1": "CAM",

        "5:1": "ST",
        "5:2": "ST"
    },

    "5-4-1": {
        "1:1": "GK",

        "2:1": "LWB",
        "2:2": "CB",
        "2:3": "CB",
        "2:4": "CB",
        "2:5": "RWB",

        "3:1": "LM",
        "3:2": "CM",
        "3:3": "CM",
        "3:4": "RM",

        "4:1": "ST"
    },

    "5-3-2": {
        "1:1": "GK",

        "2:1": "LWB",
        "2:2": "CB",
        "2:3": "CB",
        "2:4": "CB",
        "2:5": "RWB",

        "3:1": "CM",
        "3:2": "CDM",
        "3:3": "CM",

        "4:1": "ST",
        "4:2": "ST"
    },

    "5-2-3": {
        "1:1": "GK",

        "2:1": "LWB",
        "2:2": "CB",
        "2:3": "CB",
        "2:4": "CB",
        "2:5": "RWB",

        "3:1": "CM",
        "3:2": "CM",

        "4:1": "LW",
        "4:2": "ST",
        "4:3": "RW"
    },

        "4-4-1-1": {
        "1:1": "GK",

        "2:1": "LB",
        "2:2": "CB",
        "2:3": "CB",
        "2:4": "RB",

        "3:1": "LM",
        "3:2": "CM",
        "3:3": "CM",
        "3:4": "RM",

        "4:1": "CAM",

        "5:1": "ST"
    },

    "4-5-1": {
        "1:1": "GK",

        "2:1": "LB",
        "2:2": "CB",
        "2:3": "CB",
        "2:4": "RB",

        "3:1": "LM",
        "3:2": "CM",
        "3:3": "CDM",
        "3:4": "CM",
        "3:5": "RM",

        "4:1": "ST"
    },

    "4-1-3-2": {
        "1:1": "GK",

        "2:1": "LB",
        "2:2": "CB",
        "2:3": "CB",
        "2:4": "RB",

        "3:1": "CDM",

        "4:1": "LM",
        "4:2": "CM",
        "4:3": "RM",

        "5:1": "ST",
        "5:2": "ST"
    },

    "4-3-1-2": {
        "1:1": "GK",

        "2:1": "LB",
        "2:2": "CB",
        "2:3": "CB",
        "2:4": "RB",

        "3:1": "CM",
        "3:2": "CM",
        "3:3": "CM",

        "4:1": "CAM",

        "5:1": "ST",
        "5:2": "ST"
    },

    "3-5-1-1": {
        "1:1": "GK",

        "2:1": "CB",
        "2:2": "CB",
        "2:3": "CB",

        "3:1": "LWB",
        "3:2": "CM",
        "3:3": "CDM",
        "3:4": "CM",
        "3:5": "RWB",

        "4:1": "CAM",

        "5:1": "ST"
    },

    "3-1-4-2": {
        "1:1": "GK",

        "2:1": "CB",
        "2:2": "CB",
        "2:3": "CB",

        "3:1": "CDM",

        "4:1": "LM",
        "4:2": "CM",
        "4:3": "CM",
        "4:4": "RM",

        "5:1": "ST",
        "5:2": "ST"
    }

    
}


# ============================================================
# HELPERS
# ============================================================

def infer_position(formation, grid, broad_position):

    if broad_position == "G":
        return "GK"

    if not formation or not grid:
        return "Unknown"

    formation_map = POSITION_MAPS.get(formation)

    if formation_map:
        return formation_map.get(grid, "Unknown")

    return "Unknown"


def chunk_list(items, size):

    for i in range(0, len(items), size):
        yield items[i:i + size]


# ============================================================
# 1. GET COMPLETED FIXTURES
# ============================================================

print()
print("==========================================")
print("TRANSFIT AI - POSITION INFERENCE")
print("==========================================")
print()
print("Downloading completed fixtures...")

response = requests.get(
    FIXTURES_URL,
    headers=HEADERS,
    params={
        "league": LEAGUE_ID,
        "season": SEASON,
        "status": "FT-AET-PEN"
    }
)

fixture_data = response.json()

if fixture_data.get("errors"):
    print("Fixture API Error:", fixture_data["errors"])
    raise SystemExit


fixtures = fixture_data.get("response", [])

fixture_ids = [
    fixture["fixture"]["id"]
    for fixture in fixtures
]

print("Completed fixtures:", len(fixture_ids))


# ============================================================
# 2. DOWNLOAD FIXTURE DATA IN GROUPS OF 20
# ============================================================

player_positions = defaultdict(Counter)

player_names = {}

unknown_formations = Counter()

fixture_groups = list(
    chunk_list(fixture_ids, 20)
)

print("Fixture batches:", len(fixture_groups))
print()


for batch_number, fixture_group in enumerate(
    fixture_groups,
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

    data = response.json()

    if data.get("errors"):

        print(
            f"Batch {batch_number} error:",
            data["errors"]
        )

        continue


    for fixture in data.get("response", []):

        lineups = fixture.get(
            "lineups",
            []
        )

        for team_lineup in lineups:

            formation = team_lineup.get(
                "formation"
            )

            if formation not in POSITION_MAPS:
                unknown_formations[formation] += 1


            for starting_player in team_lineup.get(
                "startXI",
                []
            ):

                player = starting_player[
                    "player"
                ]

                player_id = player["id"]
                player_name = player["name"]

                grid = player.get("grid")
                broad_position = player.get("pos")


                detailed_position = infer_position(
                    formation,
                    grid,
                    broad_position
                )


                player_names[player_id] = player_name

                player_positions[
                    player_id
                ][detailed_position] += 1


    print(
        f"Batch "
        f"{batch_number}/{len(fixture_groups)} "
        f"processed"
    )

    time.sleep(0.3)


# ============================================================
# 3. CREATE PLAYER POSITION PROFILES
# ============================================================

rows = []


for player_id, position_counter in player_positions.items():

    known_positions = {
        position: count
        for position, count in position_counter.items()
        if position != "Unknown"
    }


    total_starts = sum(
        position_counter.values()
    )


    unknown_starts = position_counter.get(
        "Unknown",
        0
    )


    if known_positions:

        ranked_positions = sorted(
            known_positions.items(),
            key=lambda item: item[1],
            reverse=True
        )

        primary_position = ranked_positions[0][0]
        primary_starts = ranked_positions[0][1]


        if len(ranked_positions) >= 2:

            secondary_position = ranked_positions[1][0]
            secondary_starts = ranked_positions[1][1]

        else:

            secondary_position = None
            secondary_starts = 0


        known_total = sum(
            known_positions.values()
        )

        confidence = round(
            primary_starts
            / known_total
            * 100,
            1
        )

    else:

        primary_position = "Unknown"
        primary_starts = 0
        secondary_position = None
        secondary_starts = 0
        confidence = 0


    position_history = " | ".join(
        f"{position}:{count}"
        for position, count in position_counter.most_common()
    )


    rows.append({

        "player_id": player_id,
        "name": player_names[player_id],

        "primary_position": primary_position,
        "primary_starts": primary_starts,

        "secondary_position": secondary_position,
        "secondary_starts": secondary_starts,

        "total_starts": total_starts,

        "position_confidence": confidence,

        "unknown_starts": unknown_starts,

        "position_history": position_history
    })


# ============================================================
# 4. EXPORT
# ============================================================

df = pd.DataFrame(rows)

df = df.sort_values(
    by=[
        "primary_position",
        "position_confidence"
    ],
    ascending=[
        True,
        False
    ]
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 5. SUMMARY
# ============================================================

print()
print("==========================================")
print("POSITION DATASET CREATED")
print("==========================================")

print("Players analyzed:", len(df))
print("Output:", OUTPUT_FILE)

print()
print("Primary positions:")
print(
    df["primary_position"]
    .value_counts()
)

print()

if unknown_formations:

    print("Unmapped formations found:")

    for formation, count in unknown_formations.most_common():

        print(
            formation,
            ":",
            count
        )