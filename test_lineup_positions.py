import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")

HEADERS = {
    "x-apisports-key": API_KEY
}

FIXTURES_URL = "https://v3.football.api-sports.io/fixtures"
LINEUPS_URL = "https://v3.football.api-sports.io/fixtures/lineups"

LEAGUE_ID = 39
TEAM_ID = 42       # Arsenal
SEASON = 2024


# --------------------------------------------------
# 1. Get one Arsenal fixture
# --------------------------------------------------

fixture_response = requests.get(
    FIXTURES_URL,
    headers=HEADERS,
    params={
        "league": LEAGUE_ID,
        "season": SEASON,
        "team": TEAM_ID,
        "last": 1
    }
)

fixture_data = fixture_response.json()

if fixture_data.get("errors"):
    print("Fixture API Error:", fixture_data["errors"])
    exit()

fixtures = fixture_data.get("response", [])

if not fixtures:
    print("No fixture found.")
    exit()

fixture = fixtures[0]

fixture_id = fixture["fixture"]["id"]

home_team = fixture["teams"]["home"]["name"]
away_team = fixture["teams"]["away"]["name"]

print()
print("====================================")
print("FIXTURE FOUND")
print("====================================")

print("Fixture ID:", fixture_id)
print("Match:", home_team, "vs", away_team)
print()


# --------------------------------------------------
# 2. Get lineups
# --------------------------------------------------

lineup_response = requests.get(
    LINEUPS_URL,
    headers=HEADERS,
    params={
        "fixture": fixture_id
    }
)

lineup_data = lineup_response.json()

if lineup_data.get("errors"):
    print("Lineup API Error:", lineup_data["errors"])
    exit()

lineups = lineup_data.get("response", [])

if not lineups:
    print("No lineup data available.")
    exit()


# --------------------------------------------------
# 3. Print formations and grid positions
# --------------------------------------------------

for team_lineup in lineups:

    team = team_lineup["team"]
    formation = team_lineup["formation"]

    print()
    print("====================================")
    print(team["name"])
    print("Formation:", formation)
    print("====================================")

    print()
    print("STARTING XI")
    print("------------------------------------")

    for item in team_lineup["startXI"]:

        player = item["player"]

        print(
            f"{player['name']:<25}"
            f"Position: {player['pos']:<5}"
            f"Grid: {player['grid']}"
        )

    print()