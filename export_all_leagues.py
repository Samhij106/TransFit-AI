import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

from league_config import LEAGUES


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")

if not API_KEY:
    raise ValueError(
        "API_FOOTBALL_KEY was not found. "
        "Make sure it exists in your .env file."
    )

PLAYERS_URL = "https://v3.football.api-sports.io/players"
TEAMS_URL = "https://v3.football.api-sports.io/teams"

HEADERS = {
    "x-apisports-key": API_KEY
}

OUTPUT_DIR = Path("data/raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# GENERIC API REQUEST
# ============================================================

def api_request(url, params, retries=3):
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                params=params,
                timeout=30,
            )

            if response.status_code == 429:
                print("Rate limit reached. Waiting 5 seconds...")
                time.sleep(5)
                continue

            response.raise_for_status()

            data = response.json()

            if data.get("errors"):
                raise RuntimeError(
                    f"API error: {data['errors']}"
                )

            return data

        except requests.RequestException as error:
            print(
                f"Request failed "
                f"(attempt {attempt}/{retries}): {error}"
            )

            if attempt == retries:
                raise

            time.sleep(3)

    return {}


# ============================================================
# OFFICIAL TEAMS
# ============================================================

def get_official_teams(league_id, season):
    params = {
        "league": league_id,
        "season": season,
    }

    data = api_request(
        TEAMS_URL,
        params,
    )

    official_teams = {}

    for item in data.get("response", []):
        team = item.get("team", {})

        team_id = team.get("id")
        team_name = team.get("name")

        if team_id is not None:
            official_teams[int(team_id)] = team_name

    return official_teams


# ============================================================
# PLAYER PAGE REQUEST
# ============================================================

def request_player_page(league_id, season, page):
    params = {
        "league": league_id,
        "season": season,
        "page": page,
    }

    return api_request(
        PLAYERS_URL,
        params,
    )


# ============================================================
# EXTRACT PLAYER DATA
# ============================================================

def extract_rows(
    api_response,
    league_config,
    official_team_ids,
):
    rows = []

    expected_league_id = league_config["id"]
    expected_season = league_config["season"]

    skipped_wrong_league = 0
    skipped_wrong_season = 0
    skipped_wrong_team = 0

    for item in api_response.get("response", []):
        player = item.get("player", {})
        statistics_list = item.get("statistics", [])

        for stats in statistics_list:
            team = stats.get("team", {})
            league = stats.get("league", {})

            league_id = league.get("id")
            season = league.get("season")
            team_id = team.get("id")

            # ------------------------------------------------
            # Exact league only
            # ------------------------------------------------

            if league_id != expected_league_id:
                skipped_wrong_league += 1
                continue

            # ------------------------------------------------
            # Exact season only
            # ------------------------------------------------

            if season != expected_season:
                skipped_wrong_season += 1
                continue

            # ------------------------------------------------
            # Official participating clubs only
            # ------------------------------------------------

            if team_id not in official_team_ids:
                skipped_wrong_team += 1
                continue

            games = stats.get("games", {})
            shots = stats.get("shots", {})
            goals = stats.get("goals", {})
            passes = stats.get("passes", {})
            tackles = stats.get("tackles", {})
            duels = stats.get("duels", {})
            dribbles = stats.get("dribbles", {})
            fouls = stats.get("fouls", {})
            cards = stats.get("cards", {})

            row = {
                # League
                "league_id": league_id,
                "league": league.get("name"),
                "season": season,

                # Team
                "team_id": team_id,
                "team": team.get("name"),

                # Player
                "player_id": player.get("id"),
                "name": player.get("name"),
                "firstname": player.get("firstname"),
                "lastname": player.get("lastname"),
                "age": player.get("age"),
                "nationality": player.get("nationality"),
                "height": player.get("height"),
                "weight": player.get("weight"),
                "photo": player.get("photo"),

                # Games
                "position": games.get("position"),
                "appearances": games.get("appearences"),
                "lineups": games.get("lineups"),
                "minutes": games.get("minutes"),
                "rating": games.get("rating"),

                # Goals / assists
                "goals": goals.get("total"),
                "assists": goals.get("assists"),

                # Shooting
                "shots": shots.get("total"),
                "shots_on_target": shots.get("on"),

                # Passing
                "passes": passes.get("total"),
                "key_passes": passes.get("key"),
                "pass_accuracy": passes.get("accuracy"),

                # Defensive
                "tackles": tackles.get("total"),
                "blocks": tackles.get("blocks"),
                "interceptions": tackles.get("interceptions"),

                # Dribbling
                "dribble_attempts": dribbles.get("attempts"),
                "successful_dribbles": dribbles.get("success"),

                # Duels
                "duels_total": duels.get("total"),
                "duels_won": duels.get("won"),

                # Fouls
                "fouls_drawn": fouls.get("drawn"),
                "fouls_committed": fouls.get("committed"),

                # Cards
                "yellow_cards": cards.get("yellow"),
                "red_cards": cards.get("red"),
            }

            rows.append(row)

    skipped = {
        "wrong_league": skipped_wrong_league,
        "wrong_season": skipped_wrong_season,
        "wrong_team": skipped_wrong_team,
    }

    return rows, skipped


# ============================================================
# EXPORT ONE LEAGUE
# ============================================================

def export_league(league_config):
    league_id = league_config["id"]
    league_name = league_config["name"]
    league_key = league_config["key"]
    season = league_config["season"]

    print()
    print("=" * 70)
    print(f"EXPORTING: {league_name}")
    print(f"League ID: {league_id}")
    print(f"Season: {season}")
    print("=" * 70)

    # --------------------------------------------------------
    # Official clubs
    # --------------------------------------------------------

    official_teams = get_official_teams(
        league_id,
        season,
    )

    official_team_ids = set(
        official_teams.keys()
    )

    print(
        f"Official teams: "
        f"{len(official_team_ids)}"
    )

    if not official_team_ids:
        raise RuntimeError(
            f"No official teams found for {league_name}"
        )

    all_rows = []

    total_wrong_league = 0
    total_wrong_season = 0
    total_wrong_team = 0

    # --------------------------------------------------------
    # First player page
    # --------------------------------------------------------

    first_page = request_player_page(
        league_id,
        season,
        1,
    )

    if not first_page:
        print(
            f"No player response received "
            f"for {league_name}"
        )
        return pd.DataFrame()

    paging = first_page.get("paging", {})
    total_pages = paging.get("total", 1)

    if not total_pages:
        total_pages = 1

    print(
        f"Player pages: "
        f"{total_pages}"
    )

    first_rows, skipped = extract_rows(
        first_page,
        league_config,
        official_team_ids,
    )

    all_rows.extend(first_rows)

    total_wrong_league += skipped["wrong_league"]
    total_wrong_season += skipped["wrong_season"]
    total_wrong_team += skipped["wrong_team"]

    print(
        f"Page 1/{total_pages} "
        f"| rows added: {len(first_rows)}"
    )

    # --------------------------------------------------------
    # Remaining pages
    # --------------------------------------------------------

    for page in range(2, total_pages + 1):
        data = request_player_page(
            league_id,
            season,
            page,
        )

        rows, skipped = extract_rows(
            data,
            league_config,
            official_team_ids,
        )

        all_rows.extend(rows)

        total_wrong_league += skipped["wrong_league"]
        total_wrong_season += skipped["wrong_season"]
        total_wrong_team += skipped["wrong_team"]

        print(
            f"Page {page}/{total_pages} "
            f"| rows added: {len(rows)}"
        )

        time.sleep(0.15)

    # --------------------------------------------------------
    # DataFrame
    # --------------------------------------------------------

    df = pd.DataFrame(all_rows)

    if df.empty:
        print()
        print(
            f"WARNING: No valid players "
            f"found for {league_name}"
        )
        return df

    df = df.drop_duplicates()

    # --------------------------------------------------------
    # Final safety filtering
    # --------------------------------------------------------

    df = df[
        df["league_id"] == league_id
    ].copy()

    df = df[
        df["season"] == season
    ].copy()

    df = df[
        df["team_id"].isin(
            official_team_ids
        )
    ].copy()

    # --------------------------------------------------------
    # Save league CSV
    # --------------------------------------------------------

    output_file = (
        OUTPUT_DIR
        / f"{league_key}_players_{season}.csv"
    )

    df.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print("-" * 70)
    print(f"Saved: {output_file}")
    print(f"Rows: {len(df)}")
    print(
        f"Unique players: "
        f"{df['player_id'].nunique()}"
    )
    print(
        f"Teams: "
        f"{df['team_id'].nunique()}"
    )

    print()
    print("Filtered during extraction:")
    print(
        f"Wrong league rows: "
        f"{total_wrong_league}"
    )
    print(
        f"Wrong season rows: "
        f"{total_wrong_season}"
    )
    print(
        f"Non-official team rows: "
        f"{total_wrong_team}"
    )
    print("-" * 70)

    return df


# ============================================================
# MAIN
# ============================================================

def main():
    print()
    print("=" * 70)
    print("TRANSFIT AI")
    print("BIG FIVE LEAGUES PLAYER EXPORT")
    print("OFFICIAL TEAM FILTER ENABLED")
    print("=" * 70)

    league_dataframes = []

    # --------------------------------------------------------
    # Export all configured leagues
    # --------------------------------------------------------

    for league in LEAGUES:
        try:
            df = export_league(
                league
            )

            if not df.empty:
                league_dataframes.append(
                    df
                )

        except Exception as error:
            print()
            print("=" * 70)
            print(
                f"ERROR EXPORTING "
                f"{league['name']}"
            )
            print(error)
            print("=" * 70)

    # --------------------------------------------------------
    # Make sure export succeeded
    # --------------------------------------------------------

    if not league_dataframes:
        print()
        print(
            "No league data was exported."
        )
        return

    # --------------------------------------------------------
    # Combine Big Five
    # --------------------------------------------------------

    combined_df = pd.concat(
        league_dataframes,
        ignore_index=True,
    )

    combined_df = combined_df.drop_duplicates()

    # --------------------------------------------------------
    # Valid configured leagues only
    # --------------------------------------------------------

    valid_league_ids = {
        league["id"]
        for league in LEAGUES
    }

    combined_df = combined_df[
        combined_df["league_id"].isin(
            valid_league_ids
        )
    ].copy()

    # --------------------------------------------------------
    # Determine filename
    # --------------------------------------------------------

    seasons = sorted(
        combined_df["season"]
        .dropna()
        .unique()
        .tolist()
    )

    if len(seasons) == 1:
        combined_filename = (
            f"big_five_players_"
            f"{int(seasons[0])}.csv"
        )
    else:
        combined_filename = (
            "big_five_players.csv"
        )

    combined_path = (
        OUTPUT_DIR
        / combined_filename
    )

    # --------------------------------------------------------
    # Save combined CSV
    # --------------------------------------------------------

    combined_df.to_csv(
        combined_path,
        index=False,
        encoding="utf-8-sig",
    )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("EXPORT COMPLETE")
    print("=" * 70)

    print(
        f"Combined file: "
        f"{combined_path}"
    )

    print(
        f"Total rows: "
        f"{len(combined_df)}"
    )

    print(
        f"Unique players: "
        f"{combined_df['player_id'].nunique()}"
    )

    print(
        f"Teams: "
        f"{combined_df['team_id'].nunique()}"
    )

    print(
        f"Leagues: "
        f"{combined_df['league_id'].nunique()}"
    )

    print()
    print("=" * 70)
    print("BY LEAGUE")
    print("=" * 70)

    summary = (
        combined_df
        .groupby(
            [
                "league_id",
                "league",
            ]
        )
        .agg(
            rows=(
                "player_id",
                "size",
            ),
            unique_players=(
                "player_id",
                "nunique",
            ),
            teams=(
                "team_id",
                "nunique",
            ),
        )
        .reset_index()
    )

    print(
        summary.to_string(
            index=False
        )
    )

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()