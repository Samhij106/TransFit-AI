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

OUTPUT_FILE = (
    "data/processed/"
    "team_formation_profiles_premier_league_2025.csv"
)

os.makedirs("data/processed", exist_ok=True)


# ============================================================
# HELPERS
# ============================================================

def chunk_list(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


# ============================================================
# 1. GET COMPLETED FIXTURES
# ============================================================

print()
print("==========================================")
print("TRANSFIT AI")
print("TEAM FORMATION PROFILE")
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

data = response.json()


if data.get("errors"):
    print("Fixture API Error:", data["errors"])
    raise SystemExit


fixtures = data.get("response", [])


fixture_ids = [
    fixture["fixture"]["id"]
    for fixture in fixtures
]


print("Completed fixtures:", len(fixture_ids))


# ============================================================
# 2. FORMATION COUNTERS
# ============================================================

team_formations = defaultdict(Counter)

team_names = {}

matches_with_lineup = defaultdict(int)


# ============================================================
# 3. DOWNLOAD FIXTURES IN BATCHES
# ============================================================

fixture_batches = list(
    chunk_list(fixture_ids, 20)
)

print("Fixture batches:", len(fixture_batches))
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


    for fixture in batch_data.get("response", []):

        lineups = fixture.get(
            "lineups",
            []
        )


        for team_lineup in lineups:

            team = team_lineup.get(
                "team",
                {}
            )

            team_id = team.get("id")
            team_name = team.get("name")

            formation = team_lineup.get(
                "formation"
            )


            if not team_id or not formation:
                continue


            team_names[team_id] = team_name

            team_formations[
                team_id
            ][formation] += 1

            matches_with_lineup[
                team_id
            ] += 1


    print(
        f"Batch "
        f"{batch_number}/{len(fixture_batches)} "
        f"processed"
    )

    time.sleep(0.3)


# ============================================================
# 4. BUILD TEAM PROFILES
# ============================================================

rows = []


for team_id, formation_counter in team_formations.items():

    total_matches = sum(
        formation_counter.values()
    )


    ranked_formations = (
        formation_counter.most_common()
    )


    # --------------------------------------------------------
    # Primary formation
    # --------------------------------------------------------

    primary_formation = (
        ranked_formations[0][0]
    )

    primary_matches = (
        ranked_formations[0][1]
    )

    primary_percentage = round(
        primary_matches
        / total_matches
        * 100,
        1
    )


    # --------------------------------------------------------
    # Secondary formation
    # --------------------------------------------------------

    if len(ranked_formations) >= 2:

        secondary_formation = (
            ranked_formations[1][0]
        )

        secondary_matches = (
            ranked_formations[1][1]
        )

        secondary_percentage = round(
            secondary_matches
            / total_matches
            * 100,
            1
        )

    else:

        secondary_formation = None
        secondary_matches = 0
        secondary_percentage = 0


    # --------------------------------------------------------
    # Formation history
    # --------------------------------------------------------

    formation_history = " | ".join(

        f"{formation}:{count}"

        for formation, count
        in ranked_formations
    )


    rows.append({

        "league_id": LEAGUE_ID,
        "league": LEAGUE_NAME,
        "season": SEASON,

        "team_id": team_id,
        "team": team_names[team_id],

        "matches_analyzed": total_matches,

        "primary_formation": primary_formation,
        "primary_matches": primary_matches,
        "primary_percentage": primary_percentage,

        "secondary_formation": secondary_formation,
        "secondary_matches": secondary_matches,
        "secondary_percentage": secondary_percentage,

        "formation_history": formation_history
    })


# ============================================================
# 5. EXPORT
# ============================================================

df = pd.DataFrame(rows)


df = df.sort_values(
    by="team"
)


df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 6. SUMMARY
# ============================================================

print()
print("==========================================")
print("TEAM FORMATION PROFILES READY")
print("==========================================")

print("Teams analyzed:", len(df))
print()


for _, row in df.iterrows():

    print(
        f"{row['team']:<25}"
        f"{row['primary_formation']:<12}"
        f"{row['primary_percentage']:>5}%"
    )


print()
print("Output:", OUTPUT_FILE)
