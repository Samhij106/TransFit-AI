import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")

url = "https://v3.football.api-sports.io/players"

headers = {
    "x-apisports-key": API_KEY
}

all_players = []
page = 1

while True:
    params = {
        "team": 42,       # Arsenal
        "league": 39,     # Premier League
        "season": 2024,
        "page": page
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    for item in data.get("response", []):
        player = item["player"]

        for stats in item["statistics"]:
            games = stats["games"]

            if not games["appearences"] or games["appearences"] == 0:
                continue

            goals = stats["goals"]
            passes = stats["passes"]
            shots = stats["shots"]
            tackles = stats["tackles"]
            dribbles = stats["dribbles"]

            all_players.append({
                "player_id": player["id"],
                "name": player["name"],
                "age": player["age"],
                "position": games["position"],
                "appearances": games["appearences"],
                "minutes": games["minutes"],
                "rating": games["rating"],
                "goals": goals["total"],
                "assists": goals["assists"],
                "shots": shots["total"],
                "shots_on_target": shots["on"],
                "passes": passes["total"],
                "key_passes": passes["key"],
                "tackles": tackles["total"],
                "interceptions": tackles["interceptions"],
                "dribble_attempts": dribbles["attempts"],
                "successful_dribbles": dribbles["success"],
                "photo": player["photo"]
            })

    paging = data.get("paging", {})

    if page >= paging.get("total", 1):
        break

    page += 1

df = pd.DataFrame(all_players)

df.to_csv("arsenal_players_2024.csv", index=False)

print("CSV created successfully.")
print("Players exported:", len(df))