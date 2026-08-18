import os

import pandas as pd
import requests
from dotenv import load_dotenv

from league_config import LEAGUES


load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")

if not API_KEY:
    raise ValueError("API_FOOTBALL_KEY not found in .env")


BASE_URL = "https://v3.football.api-sports.io/teams"

HEADERS = {
    "x-apisports-key": API_KEY
}

CSV_FILE = "data/raw/big_five_players_2025.csv"


def get_official_teams(league_id, season):
    params = {
        "league": league_id,
        "season": season,
    }

    response = requests.get(
        BASE_URL,
        headers=HEADERS,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if data.get("errors"):
        raise RuntimeError(data["errors"])

    teams = {}

    for item in data.get("response", []):
        team = item.get("team", {})

        team_id = team.get("id")
        team_name = team.get("name")

        if team_id is not None:
            teams[int(team_id)] = team_name

    return teams


def main():
    df = pd.read_csv(CSV_FILE)

    df["team_id"] = pd.to_numeric(
        df["team_id"],
        errors="coerce",
    )

    print()
    print("=" * 80)
    print("TRANSFIT AI - OFFICIAL TEAM COMPARISON")
    print("=" * 80)

    for league in LEAGUES:
        league_id = league["id"]
        league_name = league["name"]
        season = league["season"]

        print()
        print("=" * 80)
        print(f"{league_name} | Season {season}")
        print("=" * 80)

        official_teams = get_official_teams(
            league_id,
            season,
        )

        league_df = df[
            df["league_id"] == league_id
        ].copy()

        csv_teams = (
            league_df[
                ["team_id", "team"]
            ]
            .dropna(subset=["team_id"])
            .drop_duplicates()
        )

        csv_team_dict = {
            int(row["team_id"]): row["team"]
            for _, row in csv_teams.iterrows()
        }

        official_ids = set(official_teams.keys())
        csv_ids = set(csv_team_dict.keys())

        extra_ids = csv_ids - official_ids
        missing_ids = official_ids - csv_ids

        print(
            f"Official teams from API: "
            f"{len(official_ids)}"
        )

        print(
            f"Teams found in player CSV: "
            f"{len(csv_ids)}"
        )

        print()

        if extra_ids:
            print("EXTRA TEAMS IN PLAYER CSV:")

            for team_id in sorted(extra_ids):
                team_name = csv_team_dict.get(
                    team_id,
                    "Unknown",
                )

                player_count = league_df[
                    league_df["team_id"] == team_id
                ]["player_id"].nunique()

                print(
                    f"  {team_id} | "
                    f"{team_name} | "
                    f"{player_count} players"
                )
        else:
            print("EXTRA TEAMS: None")

        print()

        if missing_ids:
            print("MISSING OFFICIAL TEAMS:")

            for team_id in sorted(missing_ids):
                print(
                    f"  {team_id} | "
                    f"{official_teams[team_id]}"
                )
        else:
            print("MISSING OFFICIAL TEAMS: None")

    print()
    print("=" * 80)
    print("DONE")
    print("=" * 80)


if __name__ == "__main__":
    main()