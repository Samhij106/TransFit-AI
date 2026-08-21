import argparse
import json
from pathlib import Path

import duckdb
import pandas as pd


DEFAULT_DATABASE = Path(
    "data/external/transfermarkt-datasets.duckdb"
)
DEFAULT_VALUES = Path(
    "data/processed/player_market_values_2025.csv"
)
DEFAULT_PLAYERS = Path(
    "data/processed/ml_player_context_2025.csv"
)
DEFAULT_CLUBS = Path(
    "data/processed/ml_club_context_2025.csv"
)
DEFAULT_ALIASES = Path(
    "data/processed/ml_club_aliases_2025.csv"
)


PLAYER_QUERY = """
WITH reference AS (
    SELECT MAX(date) AS reference_date
    FROM player_valuations
),
tracked AS (
    SELECT DISTINCT
        TRY_CAST(api_football_player_id AS INTEGER)
            AS api_football_player_id,
        TRY_CAST(transfermarkt_player_id AS INTEGER)
            AS transfermarkt_player_id,
        current_team,
        transfermarkt_club
    FROM tracked_players
    WHERE TRY_CAST(transfermarkt_player_id AS INTEGER)
        IS NOT NULL
),
values AS (
    SELECT
        tracked.transfermarkt_player_id,
        ARG_MAX(
            valuation.market_value_in_eur,
            valuation.date
        ) AS recent_market_value_eur,
        ARG_MIN(
            valuation.market_value_in_eur,
            ABS(DATE_DIFF(
                'day',
                valuation.date,
                reference.reference_date - INTERVAL 180 DAY
            ))
        ) FILTER (
            WHERE valuation.date <=
                reference.reference_date - INTERVAL 60 DAY
        ) AS older_market_value_eur
    FROM tracked
    CROSS JOIN reference
    LEFT JOIN player_valuations valuation
        ON valuation.player_id = tracked.transfermarkt_player_id
       AND valuation.date >=
           reference.reference_date - INTERVAL 365 DAY
       AND valuation.date <= reference.reference_date
    GROUP BY tracked.transfermarkt_player_id
),
history AS (
    SELECT
        tracked.transfermarkt_player_id,
        COUNT(transfer.player_id) AS previous_transfers_3y
    FROM tracked
    CROSS JOIN reference
    LEFT JOIN transfers transfer
        ON transfer.player_id = tracked.transfermarkt_player_id
       AND transfer.transfer_date < reference.reference_date
       AND transfer.transfer_date >=
           reference.reference_date - INTERVAL 3 YEAR
    GROUP BY tracked.transfermarkt_player_id
)
SELECT
    tracked.api_football_player_id,
    tracked.transfermarkt_player_id,
    tracked.current_team,
    tracked.transfermarkt_club,
    TRY_CAST(player.current_club_id AS INTEGER)
        AS current_club_id,
    player.position AS broad_position,
    player.sub_position,
    values.recent_market_value_eur / 1000000.0
        AS recent_market_value_m_eur,
    CASE
        WHEN values.older_market_value_eur > 0
         AND values.recent_market_value_eur > 0
        THEN 100.0 * (
            values.recent_market_value_eur
            / values.older_market_value_eur - 1
        )
        ELSE 0.0
    END AS market_value_trend_180d_pct,
    COALESCE(history.previous_transfers_3y, 0)
        AS previous_transfers_3y,
    reference.reference_date
FROM tracked
CROSS JOIN reference
JOIN players player
    ON player.player_id = tracked.transfermarkt_player_id
LEFT JOIN values USING (transfermarkt_player_id)
LEFT JOIN history USING (transfermarkt_player_id)
ORDER BY tracked.api_football_player_id
"""


CLUB_QUERY = """
WITH reference AS (
    SELECT MAX(date) AS reference_date
    FROM games
),
club_performance AS (
    SELECT
        club_game.club_id,
        COUNT(DISTINCT club_game.game_id) AS games_analyzed,
        AVG(
            CASE
                WHEN club_game.own_goals >
                    club_game.opponent_goals THEN 3.0
                WHEN club_game.own_goals =
                    club_game.opponent_goals THEN 1.0
                ELSE 0.0
            END
        ) AS points_per_game,
        AVG(
            club_game.own_goals - club_game.opponent_goals
        ) AS goal_difference_per_game
    FROM club_games club_game
    CROSS JOIN reference
    JOIN games game
        ON TRY_CAST(game.game_id AS INTEGER)
            = TRY_CAST(club_game.game_id AS INTEGER)
       AND game.date >=
           reference.reference_date - INTERVAL 365 DAY
       AND game.date <= reference.reference_date
    GROUP BY club_game.club_id
)
SELECT
    TRY_CAST(club.club_id AS INTEGER) AS club_id,
    club.name AS transfermarkt_club,
    club.domestic_competition_id,
    COALESCE(club_performance.games_analyzed, 0)
        AS games_analyzed,
    club_performance.points_per_game,
    club_performance.goal_difference_per_game,
    reference.reference_date
FROM clubs club
CROSS JOIN reference
LEFT JOIN club_performance
    ON club_performance.club_id =
        TRY_CAST(club.club_id AS INTEGER)
WHERE TRY_CAST(club.club_id AS INTEGER) IS NOT NULL
ORDER BY club_id
"""


def build_context(
    database_path,
    market_values_path,
    player_output,
    club_output,
    alias_output,
):
    tracked = pd.read_csv(
        market_values_path,
        usecols=[
            "api_football_player_id",
            "transfermarkt_player_id",
            "current_team",
            "transfermarkt_club",
        ],
    )
    connection = duckdb.connect(
        str(database_path),
        read_only=True,
    )
    try:
        connection.register("tracked_players", tracked)
        players = connection.execute(PLAYER_QUERY).fetchdf()
        clubs = connection.execute(CLUB_QUERY).fetchdf()
    finally:
        connection.close()

    aliases = (
        players.dropna(subset=["current_club_id"])
        .groupby(["current_team", "current_club_id"])
        .size()
        .reset_index(name="evidence")
        .sort_values(
            ["current_team", "evidence"],
            ascending=[True, False],
        )
        .drop_duplicates("current_team")
        .rename(columns={"current_team": "alias"})
    )
    transfermarkt_aliases = (
        players.dropna(
            subset=["transfermarkt_club", "current_club_id"]
        )
        .groupby(["transfermarkt_club", "current_club_id"])
        .size()
        .reset_index(name="evidence")
        .sort_values(
            ["transfermarkt_club", "evidence"],
            ascending=[True, False],
        )
        .drop_duplicates("transfermarkt_club")
        .rename(columns={"transfermarkt_club": "alias"})
    )
    club_name_aliases = clubs[
        ["transfermarkt_club", "club_id"]
    ].rename(columns={
        "transfermarkt_club": "alias",
        "club_id": "current_club_id",
    })
    club_name_aliases["evidence"] = 1
    aliases = pd.concat(
        [aliases, transfermarkt_aliases, club_name_aliases],
        ignore_index=True,
    ).dropna(subset=["alias", "current_club_id"])
    aliases["current_club_id"] = (
        aliases["current_club_id"].astype(int)
    )
    aliases = (
        aliases.sort_values("evidence", ascending=False)
        .drop_duplicates("alias")
        .sort_values("alias")
    )

    for path, frame in (
        (player_output, players),
        (club_output, clubs),
        (alias_output, aliases),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)

    return {
        "players": int(len(players)),
        "clubs": int(len(clubs)),
        "club_aliases": int(len(aliases)),
        "reference_date": str(players["reference_date"].iloc[0]),
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Build compact current-player and club context for "
            "online transfer-success inference."
        )
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
    )
    parser.add_argument(
        "--market-values",
        type=Path,
        default=DEFAULT_VALUES,
    )
    parser.add_argument(
        "--players-output",
        type=Path,
        default=DEFAULT_PLAYERS,
    )
    parser.add_argument(
        "--clubs-output",
        type=Path,
        default=DEFAULT_CLUBS,
    )
    parser.add_argument(
        "--aliases-output",
        type=Path,
        default=DEFAULT_ALIASES,
    )
    args = parser.parse_args()

    result = build_context(
        args.database,
        args.market_values,
        args.players_output,
        args.clubs_output,
        args.aliases_output,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
