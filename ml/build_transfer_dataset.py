import argparse
import json
from pathlib import Path

import duckdb
import pandas as pd

from ml.model_config import BIG_FIVE_COMPETITIONS, FEATURES, TARGET


DEFAULT_DATABASE = Path(
    "data/external/transfermarkt-datasets.duckdb"
)
DEFAULT_OUTPUT = Path("data/ml/transfer_success_dataset.csv")
DEFAULT_REPORT = Path("data/ml/dataset_report.json")


def build_query(min_date, max_date):
    competition_values = ", ".join(
        f"'{competition}'"
        for competition in BIG_FIVE_COMPETITIONS
    )

    return f"""
WITH deduplicated_transfers AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY
                player_id,
                transfer_date,
                from_club_id,
                to_club_id
            ORDER BY
                COALESCE(transfer_fee, 0) DESC,
                COALESCE(market_value_in_eur, 0) DESC
        ) AS duplicate_rank
    FROM transfers
),
base AS MATERIALIZED (
    SELECT
        ROW_NUMBER() OVER (
            ORDER BY
                transfer.transfer_date,
                transfer.player_id,
                transfer.from_club_id,
                transfer.to_club_id
        ) AS transfer_id,
        transfer.player_id,
        transfer.transfer_date,
        transfer.transfer_season,
        transfer.from_club_id,
        transfer.to_club_id,
        transfer.from_club_name,
        transfer.to_club_name,
        COALESCE(
            CAST(transfer.market_value_in_eur AS DOUBLE),
            0
        ) AS transfer_market_value_eur,
        player.date_of_birth,
        player.position AS broad_position,
        player.sub_position,
        source_club.domestic_competition_id
            AS from_competition_id,
        target_club.domestic_competition_id
            AS to_competition_id
    FROM deduplicated_transfers transfer
    JOIN players player
        ON player.player_id = transfer.player_id
    LEFT JOIN clubs source_club
        ON TRY_CAST(source_club.club_id AS INTEGER)
            = transfer.from_club_id
    JOIN clubs target_club
        ON TRY_CAST(target_club.club_id AS INTEGER)
            = transfer.to_club_id
    WHERE transfer.duplicate_rank = 1
      AND transfer.transfer_date BETWEEN
          DATE '{min_date}' AND DATE '{max_date}'
      AND target_club.domestic_competition_id IN (
          {competition_values}
      )
      AND transfer.player_id IS NOT NULL
      AND transfer.from_club_id IS NOT NULL
      AND transfer.to_club_id IS NOT NULL
      AND transfer.from_club_id > 0
      AND transfer.to_club_id > 0
      AND transfer.from_club_id <> transfer.to_club_id
      AND player.date_of_birth IS NOT NULL
      AND COALESCE(player.position, '') <> 'Goalkeeper'
),
pre_player AS (
    SELECT
        base.transfer_id,
        COUNT(DISTINCT appearance.appearance_id)
            AS pre_appearances,
        COUNT(DISTINCT appearance.game_id)
            AS pre_games,
        COALESCE(SUM(appearance.minutes_played), 0)
            AS pre_minutes,
        COALESCE(SUM(appearance.goals), 0) AS pre_goals,
        COALESCE(SUM(appearance.assists), 0) AS pre_assists
    FROM base
    LEFT JOIN appearances appearance
        ON appearance.player_id = base.player_id
       AND appearance.player_club_id = base.from_club_id
       AND appearance.date >=
           base.transfer_date - INTERVAL 365 DAY
       AND appearance.date < base.transfer_date
    GROUP BY base.transfer_id
),
pre_lineups AS (
    SELECT
        base.transfer_id,
        COUNT(DISTINCT lineup.game_id) AS pre_starts
    FROM base
    LEFT JOIN game_lineups lineup
        ON lineup.player_id = base.player_id
       AND lineup.club_id = base.from_club_id
       AND lineup.type = 'starting_lineup'
       AND lineup.date >=
           base.transfer_date - INTERVAL 365 DAY
       AND lineup.date < base.transfer_date
    GROUP BY base.transfer_id
),
post_player AS (
    SELECT
        base.transfer_id,
        COUNT(DISTINCT appearance.appearance_id)
            AS post_appearances,
        COUNT(DISTINCT appearance.game_id)
            AS post_games,
        COALESCE(SUM(appearance.minutes_played), 0)
            AS post_minutes,
        COALESCE(SUM(appearance.goals), 0) AS post_goals,
        COALESCE(SUM(appearance.assists), 0) AS post_assists,
        COUNT(DISTINCT appearance.game_id) FILTER (
            WHERE appearance.date >=
                base.transfer_date + INTERVAL 275 DAY
        ) AS late_period_appearances
    FROM base
    LEFT JOIN appearances appearance
        ON appearance.player_id = base.player_id
       AND appearance.player_club_id = base.to_club_id
       AND appearance.date >= base.transfer_date
       AND appearance.date <
           base.transfer_date + INTERVAL 365 DAY
    GROUP BY base.transfer_id
),
post_lineups AS (
    SELECT
        base.transfer_id,
        COUNT(DISTINCT lineup.game_id) AS post_starts
    FROM base
    LEFT JOIN game_lineups lineup
        ON lineup.player_id = base.player_id
       AND lineup.club_id = base.to_club_id
       AND lineup.type = 'starting_lineup'
       AND lineup.date >= base.transfer_date
       AND lineup.date <
           base.transfer_date + INTERVAL 365 DAY
    GROUP BY base.transfer_id
),
pre_source_team AS (
    SELECT
        base.transfer_id,
        COUNT(DISTINCT club_game.game_id) AS source_team_games,
        AVG(
            CASE
                WHEN club_game.own_goals >
                    club_game.opponent_goals THEN 3.0
                WHEN club_game.own_goals =
                    club_game.opponent_goals THEN 1.0
                ELSE 0.0
            END
        ) AS from_points_per_game,
        AVG(
            club_game.own_goals - club_game.opponent_goals
        ) AS from_goal_difference_per_game
    FROM base
    LEFT JOIN club_games club_game
        ON club_game.club_id = base.from_club_id
    LEFT JOIN games game
        ON TRY_CAST(game.game_id AS INTEGER)
            = TRY_CAST(club_game.game_id AS INTEGER)
       AND game.date >=
           base.transfer_date - INTERVAL 365 DAY
       AND game.date < base.transfer_date
    WHERE game.game_id IS NOT NULL
       OR club_game.game_id IS NULL
    GROUP BY base.transfer_id
),
pre_target_team AS (
    SELECT
        base.transfer_id,
        COUNT(DISTINCT club_game.game_id) AS target_pre_games,
        AVG(
            CASE
                WHEN club_game.own_goals >
                    club_game.opponent_goals THEN 3.0
                WHEN club_game.own_goals =
                    club_game.opponent_goals THEN 1.0
                ELSE 0.0
            END
        ) AS to_points_per_game,
        AVG(
            club_game.own_goals - club_game.opponent_goals
        ) AS to_goal_difference_per_game
    FROM base
    LEFT JOIN club_games club_game
        ON club_game.club_id = base.to_club_id
    LEFT JOIN games game
        ON TRY_CAST(game.game_id AS INTEGER)
            = TRY_CAST(club_game.game_id AS INTEGER)
       AND game.date >=
           base.transfer_date - INTERVAL 365 DAY
       AND game.date < base.transfer_date
    WHERE game.game_id IS NOT NULL
       OR club_game.game_id IS NULL
    GROUP BY base.transfer_id
),
post_target_team AS (
    SELECT
        base.transfer_id,
        COUNT(DISTINCT club_game.game_id) AS target_post_games
    FROM base
    LEFT JOIN club_games club_game
        ON club_game.club_id = base.to_club_id
    LEFT JOIN games game
        ON TRY_CAST(game.game_id AS INTEGER)
            = TRY_CAST(club_game.game_id AS INTEGER)
       AND game.date >= base.transfer_date
       AND game.date <
           base.transfer_date + INTERVAL 365 DAY
    WHERE game.game_id IS NOT NULL
       OR club_game.game_id IS NULL
    GROUP BY base.transfer_id
),
pre_values AS (
    SELECT
        base.transfer_id,
        ARG_MAX(
            valuation.market_value_in_eur,
            valuation.date
        ) AS recent_market_value_eur,
        ARG_MIN(
            valuation.market_value_in_eur,
            ABS(DATE_DIFF(
                'day',
                valuation.date,
                base.transfer_date - INTERVAL 180 DAY
            ))
        ) FILTER (
            WHERE valuation.date <=
                base.transfer_date - INTERVAL 60 DAY
        ) AS older_market_value_eur
    FROM base
    LEFT JOIN player_valuations valuation
        ON valuation.player_id = base.player_id
       AND valuation.date >=
           base.transfer_date - INTERVAL 365 DAY
       AND valuation.date <= base.transfer_date
    GROUP BY base.transfer_id
),
post_values AS (
    SELECT
        base.transfer_id,
        ARG_MIN(
            valuation.market_value_in_eur,
            ABS(DATE_DIFF(
                'day',
                valuation.date,
                base.transfer_date + INTERVAL 365 DAY
            ))
        ) AS post_market_value_eur
    FROM base
    LEFT JOIN player_valuations valuation
        ON valuation.player_id = base.player_id
       AND valuation.date >=
           base.transfer_date + INTERVAL 180 DAY
       AND valuation.date <=
           base.transfer_date + INTERVAL 540 DAY
    GROUP BY base.transfer_id
),
transfer_history AS (
    SELECT
        base.transfer_id,
        COUNT(history.player_id) AS previous_transfers_3y
    FROM base
    LEFT JOIN transfers history
        ON history.player_id = base.player_id
       AND history.transfer_date < base.transfer_date
       AND history.transfer_date >=
           base.transfer_date - INTERVAL 3 YEAR
    GROUP BY base.transfer_id
),
features AS (
    SELECT
        base.*,
        DATE_DIFF(
            'year',
            CAST(base.date_of_birth AS DATE),
            base.transfer_date
        ) AS age_at_transfer,
        COALESCE(
            pre_values.recent_market_value_eur,
            NULLIF(base.transfer_market_value_eur, 0)
        ) / 1000000.0 AS market_value_m_eur,
        CASE
            WHEN pre_values.older_market_value_eur > 0
             AND pre_values.recent_market_value_eur > 0
            THEN 100.0 * (
                pre_values.recent_market_value_eur
                / pre_values.older_market_value_eur - 1
            )
            ELSE 0.0
        END AS market_value_trend_180d_pct,
        COALESCE(pre_player.pre_appearances, 0)
            AS pre_appearances,
        COALESCE(pre_lineups.pre_starts, 0) AS pre_starts,
        COALESCE(pre_player.pre_minutes, 0) AS pre_minutes,
        COALESCE(pre_player.pre_goals, 0) AS pre_goals,
        COALESCE(pre_player.pre_assists, 0) AS pre_assists,
        CASE
            WHEN pre_player.pre_minutes > 0
            THEN 90.0 * (
                pre_player.pre_goals + pre_player.pre_assists
            ) / pre_player.pre_minutes
            ELSE 0.0
        END AS pre_goal_assist_per90,
        LEAST(
            COALESCE(pre_player.pre_minutes, 0)
            / NULLIF(
                pre_source_team.source_team_games * 90.0,
                0
            ),
            1.0
        ) AS pre_minutes_share,
        LEAST(
            COALESCE(pre_lineups.pre_starts, 0)
            / NULLIF(
                pre_source_team.source_team_games * 1.0,
                0
            ),
            1.0
        ) AS pre_start_share,
        pre_source_team.from_points_per_game,
        pre_target_team.to_points_per_game,
        pre_source_team.from_goal_difference_per_game,
        pre_target_team.to_goal_difference_per_game,
        (
            CASE base.to_competition_id
                WHEN 'GB1' THEN 100.0
                WHEN 'ES1' THEN 92.0
                WHEN 'IT1' THEN 86.0
                WHEN 'L1' THEN 82.0
                WHEN 'FR1' THEN 76.0
                ELSE 60.0
            END
            -
            CASE base.from_competition_id
                WHEN 'GB1' THEN 100.0
                WHEN 'ES1' THEN 92.0
                WHEN 'IT1' THEN 86.0
                WHEN 'L1' THEN 82.0
                WHEN 'FR1' THEN 76.0
                ELSE 60.0
            END
        ) AS league_strength_gap,
        COALESCE(transfer_history.previous_transfers_3y, 0)
            AS previous_transfers_3y,
        CASE
            WHEN COALESCE(base.from_competition_id, '')
                <> base.to_competition_id THEN 1
            ELSE 0
        END AS is_cross_border,
        CASE
            WHEN EXTRACT(MONTH FROM base.transfer_date)
                IN (1, 2) THEN 1
            ELSE 0
        END AS is_winter_window,
        COALESCE(post_player.post_appearances, 0)
            AS post_appearances,
        COALESCE(post_lineups.post_starts, 0) AS post_starts,
        COALESCE(post_player.post_minutes, 0) AS post_minutes,
        COALESCE(post_player.post_goals, 0) AS post_goals,
        COALESCE(post_player.post_assists, 0) AS post_assists,
        COALESCE(post_player.late_period_appearances, 0)
            AS late_period_appearances,
        COALESCE(post_target_team.target_post_games, 0)
            AS target_post_games,
        post_values.post_market_value_eur,
        COALESCE(
            pre_values.recent_market_value_eur,
            NULLIF(base.transfer_market_value_eur, 0)
        ) AS label_pre_market_value_eur
    FROM base
    LEFT JOIN pre_player USING (transfer_id)
    LEFT JOIN pre_lineups USING (transfer_id)
    LEFT JOIN post_player USING (transfer_id)
    LEFT JOIN post_lineups USING (transfer_id)
    LEFT JOIN pre_source_team USING (transfer_id)
    LEFT JOIN pre_target_team USING (transfer_id)
    LEFT JOIN post_target_team USING (transfer_id)
    LEFT JOIN pre_values USING (transfer_id)
    LEFT JOIN post_values USING (transfer_id)
    LEFT JOIN transfer_history USING (transfer_id)
),
outcomes AS (
    SELECT
        *,
        LEAST(
            post_minutes
            / NULLIF(target_post_games * 90.0, 0),
            1.0
        ) AS outcome_minutes_share,
        LEAST(
            post_starts
            / NULLIF(target_post_games * 1.0, 0),
            1.0
        ) AS outcome_start_share,
        LEAST(
            post_appearances
            / NULLIF(target_post_games * 1.0, 0),
            1.0
        ) AS outcome_appearance_share,
        CASE
            WHEN label_pre_market_value_eur > 0
             AND post_market_value_eur > 0
            THEN LEAST(
                GREATEST(
                    0.5 + 0.35 * LN(
                        post_market_value_eur
                        / label_pre_market_value_eur
                    ),
                    0.0
                ),
                1.0
            )
            ELSE 0.5
        END AS outcome_value_score,
        CASE
            WHEN late_period_appearances > 0 THEN 1.0
            ELSE 0.0
        END AS outcome_retention
    FROM features
),
labeled AS (
    SELECT
        *,
        100.0 * (
            0.50 * COALESCE(outcome_minutes_share, 0)
            + 0.25 * COALESCE(outcome_start_share, 0)
            + 0.10 * COALESCE(outcome_appearance_share, 0)
            + 0.10 * outcome_value_score
            + 0.05 * outcome_retention
        ) AS success_score
    FROM outcomes
)
SELECT
    transfer_id,
    player_id,
    transfer_date,
    transfer_season,
    from_club_id,
    to_club_id,
    from_club_name,
    to_club_name,
    {", ".join(FEATURES)},
    post_appearances,
    post_starts,
    post_minutes,
    post_goals,
    post_assists,
    target_post_games,
    outcome_minutes_share,
    outcome_start_share,
    outcome_appearance_share,
    outcome_value_score,
    outcome_retention,
    success_score,
    CASE WHEN success_score >= 60 THEN 1 ELSE 0 END
        AS successful_transfer,
    CONCAT(
        CAST(to_club_id AS VARCHAR),
        ':',
        COALESCE(transfer_season, 'unknown')
    ) AS ranking_group
FROM labeled
WHERE age_at_transfer BETWEEN 16 AND 39
  AND target_post_games >= 20
  AND transfer_date <= (
      SELECT MAX(date) - INTERVAL 365 DAY
      FROM appearances
  )
ORDER BY transfer_date, transfer_id
"""


def build_dataset(database_path, output_path, min_date, max_date):
    connection = duckdb.connect(
        str(database_path),
        read_only=True,
    )
    try:
        dataset = connection.execute(
            build_query(min_date, max_date)
        ).fetchdf()
    finally:
        connection.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(output_path, index=False)
    return dataset


def dataset_report(dataset):
    transfer_dates = pd.to_datetime(
        dataset["transfer_date"],
        errors="coerce",
    )
    return {
        "rows": int(len(dataset)),
        "players": int(dataset["player_id"].nunique()),
        "target_clubs": int(dataset["to_club_id"].nunique()),
        "date_min": transfer_dates.min().date().isoformat(),
        "date_max": transfer_dates.max().date().isoformat(),
        "mean_success_score": round(
            float(dataset[TARGET].mean()),
            3,
        ),
        "successful_transfer_rate": round(
            float(dataset["successful_transfer"].mean()),
            4,
        ),
        "features": FEATURES,
        "missing_rate": {
            feature: round(float(dataset[feature].isna().mean()), 4)
            for feature in FEATURES
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Build a leakage-safe historical transfer success "
            "training dataset."
        )
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT,
    )
    parser.add_argument("--min-date", default="2014-07-01")
    parser.add_argument("--max-date", default="2025-06-30")
    args = parser.parse_args()

    if not args.database.exists():
        raise SystemExit(
            f"Historical database not found: {args.database}"
        )

    dataset = build_dataset(
        args.database,
        args.output,
        args.min_date,
        args.max_date,
    )
    report = dataset_report(dataset)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
