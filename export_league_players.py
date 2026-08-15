import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")

HEADERS = {
    "x-apisports-key": API_KEY
}

LEAGUE_ID = 39
LEAGUE_NAME = "Premier League"
SEASON = 2024

TEAMS_URL = "https://v3.football.api-sports.io/teams"
PLAYERS_URL = "https://v3.football.api-sports.io/players"

OUTPUT_FILE = "data/raw/premier_league_players_2024.csv"
PROGRESS_FILE = "data/raw/completed_teams.txt"

os.makedirs("data/raw", exist_ok=True)


def safe_value(value, default=0):
    return default if value is None else value


def api_request(url, params):

    while True:

        response = requests.get(
            url,
            headers=HEADERS,
            params=params
        )

        data = response.json()

        errors = data.get("errors", {})

        # Rate limit reached
        if isinstance(errors, dict) and "rateLimit" in errors:

            print()
            print("Rate limit reached.")
            print("Waiting 65 seconds...")
            print()

            time.sleep(65)
            continue

        # Wait between successful API calls
        time.sleep(7)

        return data


# --------------------------------------------------
# Load previously completed teams
# --------------------------------------------------

completed_teams = set()

if os.path.exists(PROGRESS_FILE):

    with open(PROGRESS_FILE, "r") as file:

        for line in file:
            completed_teams.add(int(line.strip()))


# --------------------------------------------------
# Load existing dataset if available
# --------------------------------------------------

if os.path.exists(OUTPUT_FILE):
    existing_df = pd.read_csv(OUTPUT_FILE)
    players_data = existing_df.to_dict("records")
else:
    players_data = []


# --------------------------------------------------
# Get Premier League teams
# --------------------------------------------------

print("Downloading team list...")

teams_data = api_request(
    TEAMS_URL,
    {
        "league": LEAGUE_ID,
        "season": SEASON
    }
)

if teams_data.get("errors"):
    print("Teams API Error:", teams_data["errors"])
    exit()


teams = []

for item in teams_data.get("response", []):

    teams.append({
        "id": item["team"]["id"],
        "name": item["team"]["name"]
    })


print("Teams found:", len(teams))
print()


# --------------------------------------------------
# Download players team by team
# --------------------------------------------------

for index, team in enumerate(teams, start=1):

    team_id = team["id"]
    team_name = team["name"]

    # Skip teams already downloaded
    if team_id in completed_teams:

        print(
            f"[{index}/{len(teams)}] "
            f"{team_name} already downloaded - skipping"
        )

        continue


    print()
    print(
        f"[{index}/{len(teams)}] "
        f"Downloading {team_name}..."
    )


    page = 1

    while page <= 3:

        data = api_request(
            PLAYERS_URL,
            {
                "team": team_id,
                "league": LEAGUE_ID,
                "season": SEASON,
                "page": page
            }
        )


        if data.get("errors"):

            print(
                f"API Error for {team_name}:",
                data["errors"]
            )

            break


        results = data.get("response", [])

        if not results:
            break


        for item in results:

            player = item["player"]

            for stats in item["statistics"]:

                games = stats["games"]
                goals = stats["goals"]
                shots = stats["shots"]
                passes = stats["passes"]
                tackles = stats["tackles"]
                dribbles = stats["dribbles"]

                appearances = safe_value(
                    games["appearences"]
                )

                minutes = safe_value(
                    games["minutes"]
                )

                if appearances == 0:
                    continue


                players_data.append({

                    "league_id": LEAGUE_ID,
                    "league": LEAGUE_NAME,
                    "season": SEASON,

                    "team_id": team_id,
                    "team": team_name,

                    "player_id": player["id"],
                    "name": player["name"],
                    "age": player["age"],
                    "nationality": player["nationality"],
                    "photo": player["photo"],

                    "position": games["position"],
                    "appearances": appearances,
                    "minutes": minutes,
                    "rating": games["rating"],

                    "goals": safe_value(
                        goals["total"]
                    ),

                    "assists": safe_value(
                        goals["assists"]
                    ),

                    "shots": safe_value(
                        shots["total"]
                    ),

                    "shots_on_target": safe_value(
                        shots["on"]
                    ),

                    "passes": safe_value(
                        passes["total"]
                    ),

                    "key_passes": safe_value(
                        passes["key"]
                    ),

                    "tackles": safe_value(
                        tackles["total"]
                    ),

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

        current_page = paging.get(
            "current",
            page
        )

        total_pages = paging.get(
            "total",
            1
        )

        print(
            f"   Page {current_page}/{total_pages}"
        )


        if current_page >= total_pages:
            break

        page += 1


    # --------------------------------------------------
    # Mark team as completed
    # --------------------------------------------------

    completed_teams.add(team_id)

    with open(PROGRESS_FILE, "a") as file:
        file.write(str(team_id) + "\n")


    # --------------------------------------------------
    # Save after every team
    # --------------------------------------------------

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

    print(
        f"   Saved. Total players: {len(df)}"
    )


# --------------------------------------------------
# Add per-90 statistics
# --------------------------------------------------

df = pd.read_csv(OUTPUT_FILE)

per90_columns = [
    "goals",
    "assists",
    "shots",
    "shots_on_target",
    "key_passes",
    "tackles",
    "interceptions",
    "dribble_attempts",
    "successful_dribbles"
]


for column in per90_columns:

    df[column + "_per90"] = (
        df[column]
        / df["minutes"]
        * 90
    ).where(
        df["minutes"] > 0,
        0
    ).round(3)


df.to_csv(
    OUTPUT_FILE,
    index=False
)


print()
print("================================")
print("DOWNLOAD COMPLETE")
print("================================")
print("Players:", len(df))
print("Teams:", df["team"].nunique())
print("File:", OUTPUT_FILE)