import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")

url = "https://v3.football.api-sports.io/teams"

headers = {
    "x-apisports-key": API_KEY
}

params = {
    "league": 39,
    "season": 2025
}

response = requests.get(url, headers=headers, params=params)

data = response.json()

print("HTTP Status:", response.status_code)
print("Errors:", data.get("errors"))
print("Results:", data.get("results"))

print("\nTeams:\n")

for item in data.get("response", []):
    team = item["team"]
    print(team["id"], "-", team["name"])