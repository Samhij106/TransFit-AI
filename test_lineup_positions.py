import os
import requests
from dotenv import load_dotenv

# --------------------------------------------------
# Load API key
# --------------------------------------------------

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")

HEADERS = {
    "x-apisports-key": API_KEY
}

FIXTURES_URL = "https://v3.football.api-sports.io/fixtures"
LINEUPS_URL = "https://v3.football.api-sports.io/fixtures/lineups"

LEAGUE_ID = 39       # Premier League
TEAM_ID = 42         # Arsenal
SEASON = 2025


# --------------------------------------------------
# Convert formation + grid into detailed position
# --------------------------------------------------

def infer_detailed_position(formation, grid):

    if not grid:
        return "Unknown"

    position_maps = {

        # ==========================================
        # 4-2-3-1
        # ==========================================

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

        # ==========================================
        # 4-3-3
        # ==========================================

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

        # ==========================================
        # 4-4-2
        # ==========================================

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

        # ==========================================
        # 4-1-4-1
        # ==========================================

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

        # ==========================================
        # 3-4-2-1
        # ==========================================

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

        # ==========================================
        # 3-5-2
        # ==========================================

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
        }
    }

    formation_map = position_maps.get(formation)

    if formation_map is None:
        return "Unknown"

    return formation_map.get(grid, "Unknown")


# --------------------------------------------------
# 1. Get completed fixtures for Arsenal
# --------------------------------------------------

fixture_response = requests.get(
    FIXTURES_URL,
    headers=HEADERS,
    params={
        "league": LEAGUE_ID,
        "season": SEASON,
        "team": TEAM_ID,
        "status": "FT"
    }
)

fixture_data = fixture_response.json()


if fixture_data.get("errors"):
    print(
        "Fixture API Error:",
        fixture_data["errors"]
    )
    exit()


fixtures = fixture_data.get("response", [])


if not fixtures:
    print("No completed fixtures found.")
    exit()


# --------------------------------------------------
# 2. Select one completed fixture
# --------------------------------------------------

fixture = fixtures[-1]

fixture_id = fixture["fixture"]["id"]

home_team = fixture["teams"]["home"]["name"]
away_team = fixture["teams"]["away"]["name"]


print()
print("==========================================")
print("TRANSFIT AI - POSITION TEST")
print("==========================================")

print("Fixture ID:", fixture_id)
print("Match:", home_team, "vs", away_team)

print()


# --------------------------------------------------
# 3. Download lineups
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
    print(
        "Lineup API Error:",
        lineup_data["errors"]
    )
    exit()


lineups = lineup_data.get("response", [])


if not lineups:
    print("No lineup data available.")
    exit()


# --------------------------------------------------
# 4. Display starting XI
# --------------------------------------------------

for team_lineup in lineups:

    team_name = team_lineup["team"]["name"]

    formation = team_lineup["formation"]


    print()
    print("==========================================")
    print(team_name)
    print("Formation:", formation)
    print("==========================================")

    print()

    print(
        f"{'Player':<25}"
        f"{'Grid':<10}"
        f"{'Broad':<10}"
        f"{'Detailed'}"
    )

    print("-" * 60)


    for item in team_lineup["startXI"]:

        player = item["player"]

        grid = player["grid"]

        broad_position = player["pos"]

        detailed_position = infer_detailed_position(
            formation,
            grid
        )


        print(
            f"{player['name']:<25}"
            f"{str(grid):<10}"
            f"{str(broad_position):<10}"
            f"{detailed_position}"
        )


    print()


print()
print("==========================================")
print("POSITION TEST COMPLETE")
print("==========================================")