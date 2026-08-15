import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")

URL = "https://v3.football.api-sports.io/players"

HEADERS = {
    "x-apisports-key": API_KEY
}

LEAGUE_ID = 39
LEAGUE_NAME = "Premier League"
SEASON = 2025

OUTPUT_FILE = "data/raw/premier_league_players_2025.csv"

os.makedirs("data/raw", exist_ok=True)


def safe_value(value, default=0):
    return default if value is None else value


players_data = []
page = 1

print(f"Downloading {LEAGUE_NAME} {SEASON}/26...")
print()


while True:

    params = {
        "league": LEAGUE_ID,
        "season": SEASON,
        "page": page
    }

    response = requests.get(
        URL,
        headers=HEADERS,
        params=params
    )

    data = response.json()

    if response.status_code != 200:
        print("HTTP Error:", response.status_code)
        break

    if data.get("errors"):
        print("API Error:", data["errors"])
        break

    for item in data.get("response", []):

        player = item["player"]

        for stats in item["statistics"]:

            games = stats["games"]
            team = stats["team"]
            goals = stats["goals"]
            shots = stats["shots"]
            passes = stats["passes"]
            tackles = stats["tackles"]
            dribbles = stats["dribbles"]

            appearances = safe_value(games["appearences"])
            minutes = safe_value(games["minutes"])

            if appearances == 0:
                continue

            players_data.append({
                "league_id": LEAGUE_ID,
                "league": LEAGUE_NAME,
                "season": SEASON,

                "team_id": team["id"],
                "team": team["name"],

                "player_id": player["id"],
                "name": player["name"],
                "age": player["age"],
                "nationality": player["nationality"],
                "photo": player["photo"],

                "position": games["position"],
                "appearances": appearances,
                "minutes": minutes,
                "rating": games["rating"],

                "goals": safe_value(goals["total"]),
                "assists": safe_value(goals["assists"]),

                "shots": safe_value(shots["total"]),
                "shots_on_target": safe_value(shots["on"]),

                "passes": safe_value(passes["total"]),
                "key_passes": safe_value(passes["key"]),

                "tackles": safe_value(tackles["total"]),
                "interceptions": safe_value(
                    tackles["interceptions"]
                ),

                "dribble_attempts": safe_value(
                    dribbles["attempts"]
                ),
                "successful_dribbles": safe_value(
                    dribbles["success"]
                )
            })

    paging = data.get("paging", {})

    current_page = paging.get("current", page)
    total_pages = paging.get("total", 1)

    print(
        f"Page {current_page}/{total_pages} "
        f"- collected: {len(players_data)}"
    )

    if current_page >= total_pages:
        break

    page += 1

    # Small delay - no need for the old 7-second workaround
    time.sleep(0.3)


df = pd.DataFrame(players_data)

df = df.drop_duplicates(
    subset=[
        "player_id",
        "team_id",
        "season"
    ]
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("==============================")
print("DOWNLOAD COMPLETE")
print("==============================")
print("Players:", len(df))
print("Teams:", df["team"].nunique())
print("Pages:", page)
print("File:", OUTPUT_FILE)