import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")

TEAM_ID = 42  # Arsenal

url = "https://v3.football.api-sports.io/players/squads"

headers = {
    "x-apisports-key": API_KEY
}

params = {
    "team": TEAM_ID
}

response = requests.get(url, headers=headers, params=params)
data = response.json()

print("HTTP Status:", response.status_code)
print("Errors:", data.get("errors"))
print()

for team_data in data.get("response", []):
    print("Team:", team_data["team"]["name"])
    print("------------------------------")

    for player in team_data["players"]:
        print(
            player["id"],
            "-",
            player["name"],
            "|",
            player["position"],
            "| Age:",
            player["age"]
        )