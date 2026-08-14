import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")

url = "https://v3.football.api-sports.io/players"

headers = {
    "x-apisports-key": API_KEY
}

params = {
    "team": 42,       # Arsenal
    "league": 39,     # Premier League
    "season": 2024
}

response = requests.get(
    url,
    headers=headers,
    params=params
)

data = response.json()

print("HTTP Status:", response.status_code)
print("Errors:", data.get("errors"))
print("Results:", data.get("results"))
print()


for item in data.get("response", []):

    player = item["player"]

    for stats in item["statistics"]:

        games = stats["games"]

        # Skip players who did not play
        if not games["appearences"] or games["appearences"] == 0:
            continue

        goals = stats["goals"]
        passes = stats["passes"]
        shots = stats["shots"]
        tackles = stats["tackles"]
        dribbles = stats["dribbles"]

        print("=" * 60)

        print("Player:", player["name"])
        print("Age:", player["age"])
        print("Photo:", player["photo"])

        print("Team:", stats["team"]["name"])
        print("League:", stats["league"]["name"])
        print("Position:", games["position"])

        print("Appearances:", games["appearences"])
        print("Minutes:", games["minutes"])
        print("Rating:", games["rating"])

        print("Goals:", goals["total"])
        print("Assists:", goals["assists"])

        print("Shots:", shots["total"])
        print("Shots on target:", shots["on"])

        print("Passes:", passes["total"])
        print("Key passes:", passes["key"])
        print("Pass accuracy:", passes["accuracy"])

        print("Tackles:", tackles["total"])
        print("Interceptions:", tackles["interceptions"])

        print("Dribble attempts:", dribbles["attempts"])
        print("Successful dribbles:", dribbles["success"])

        print()