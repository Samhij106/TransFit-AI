from pathlib import Path

import numpy as np
import pandas as pd


CURRENT_SEASON = 2025
RECENT_SEASONS = {
    2025: 1.00,
    2024: 0.55,
    2023: 0.30,
}

PROFILES_PATH = Path(
    "data/processed/player_profiles_2025.csv"
)
MARKET_VALUES_PATH = Path(
    "data/processed/player_market_values_2025.csv"
)
TRANSFERMARKT_DIR = Path(
    "data/external/transfermarkt"
)
PLAYERS_PATH = TRANSFERMARKT_DIR / "players.csv.gz"
APPEARANCES_PATH = (
    TRANSFERMARKT_DIR / "appearances.csv.gz"
)
GAMES_PATH = TRANSFERMARKT_DIR / "games.csv.gz"
LINEUPS_PATH = (
    TRANSFERMARKT_DIR / "game_lineups.csv.gz"
)
OUTPUT_PATH = Path(
    "data/processed/player_realism_profiles_2025.csv"
)

EUROPE_WEIGHTS = {
    "CL": 1.20,
    "EL": 1.10,
    "UCOL": 1.00,
}

DOMESTIC_LEAGUE_WEIGHTS = {
    "GB1": 1.08,
    "ES1": 1.04,
    "IT1": 1.02,
    "L1": 1.00,
    "FR1": 0.98,
}

POSITION_MAP = {
    "Goalkeeper": "GK",
    "Centre-Back": "CB",
    "Left-Back": "LB",
    "Right-Back": "RB",
    "Defensive Midfield": "CDM",
    "Central Midfield": "CM",
    "Attacking Midfield": "CAM",
    "Left Midfield": "LM",
    "Right Midfield": "RM",
    "Left Winger": "LW",
    "Right Winger": "RW",
    "Second Striker": "ST",
    "Centre-Forward": "ST",
}

GROUP_MAP = {
    "GK": "GK",
    "CB": "CB",
    "LB": "FB",
    "RB": "FB",
    "LWB": "FB",
    "RWB": "FB",
    "CDM": "DM",
    "CM": "CM",
    "CAM": "AM",
    "LM": "W",
    "RM": "W",
    "LW": "W",
    "RW": "W",
    "ST": "FW",
    "FB": "FB",
    "W": "W",
    "DEF": "CB",
    "MID": "CM",
    "ATT": "FW",
}

BROAD_GROUP_MAP = {
    "Goalkeeper": "GK",
    "Defender": "CB",
    "Midfielder": "CM",
    "Attacker": "FW",
}

ATTACK_GROUPS = {"FW", "W", "AM"}
MIDFIELD_GROUPS = {"CM", "DM"}


def percentile(series):
    numeric = pd.to_numeric(
        series,
        errors="coerce",
    ).fillna(0)

    return numeric.rank(
        pct=True,
        method="average",
    ) * 100


def competition_weight(row):
    competition_id = str(
        row["competition_id"]
    )
    competition_type = str(
        row["competition_type"]
    )

    if competition_id in EUROPE_WEIGHTS:
        return EUROPE_WEIGHTS[
            competition_id
        ]

    if competition_id in DOMESTIC_LEAGUE_WEIGHTS:
        return DOMESTIC_LEAGUE_WEIGHTS[
            competition_id
        ]

    if competition_type == "domestic_cup":
        return 0.90

    if competition_type == "domestic_league":
        return 0.78

    if competition_type == "international_cup":
        return 0.85

    return 0.75


def load_identity_data():
    profiles = pd.read_csv(
        PROFILES_PATH
    ).drop_duplicates(
        subset=["player_id"],
        keep="first",
    )

    market_values = pd.read_csv(
        MARKET_VALUES_PATH
    )[[
        "api_football_player_id",
        "transfermarkt_player_id",
        "market_value_m_eur",
    ]]

    players = pd.read_csv(
        PLAYERS_PATH,
        usecols=[
            "player_id",
            "sub_position",
            "position",
            "contract_expiration_date",
        ],
    ).rename(columns={
        "player_id": "transfermarkt_player_id",
        "sub_position": "transfermarkt_position",
        "position": "transfermarkt_position_group",
    })

    identities = profiles.merge(
        market_values,
        left_on="player_id",
        right_on="api_football_player_id",
        how="left",
    ).merge(
        players,
        on="transfermarkt_player_id",
        how="left",
    )

    return identities


def load_recent_games():
    games = pd.read_csv(
        GAMES_PATH,
        usecols=[
            "game_id",
            "competition_id",
            "season",
            "competition_type",
        ],
    )
    games = games[
        games["season"].isin(
            RECENT_SEASONS
        )
    ].copy()
    games = games[
        games["competition_type"]
        != "national_team_competition"
    ].copy()
    games["competition_weight"] = (
        games.apply(
            competition_weight,
            axis=1,
        )
    )

    return games


def load_relevant_appearances(
    transfermarkt_ids,
    games,
):
    game_ids = set(
        games["game_id"].astype(int)
    )
    chunks = []

    for chunk in pd.read_csv(
        APPEARANCES_PATH,
        usecols=[
            "game_id",
            "player_id",
            "goals",
            "assists",
            "minutes_played",
        ],
        chunksize=250_000,
    ):
        relevant = chunk[
            chunk["player_id"].isin(
                transfermarkt_ids
            )
            & chunk["game_id"].isin(
                game_ids
            )
        ]

        if not relevant.empty:
            chunks.append(relevant)

    if not chunks:
        return pd.DataFrame()

    appearances = pd.concat(
        chunks,
        ignore_index=True,
    ).merge(
        games,
        on="game_id",
        how="inner",
    )

    appearances["weighted_goals"] = (
        appearances["goals"]
        * appearances["competition_weight"]
    )
    appearances["weighted_assists"] = (
        appearances["assists"]
        * appearances["competition_weight"]
    )
    appearances["weighted_minutes"] = (
        appearances["minutes_played"]
        * appearances["competition_weight"]
    )

    return appearances


def load_relevant_lineups(
    transfermarkt_ids,
    games,
):
    game_ids = set(
        games["game_id"].astype(int)
    )
    game_seasons = games.set_index(
        "game_id"
    )["season"]
    chunks = []

    for chunk in pd.read_csv(
        LINEUPS_PATH,
        usecols=[
            "game_id",
            "player_id",
            "type",
            "position",
        ],
        chunksize=250_000,
    ):
        relevant = chunk[
            chunk["player_id"].isin(
                transfermarkt_ids
            )
            & chunk["game_id"].isin(
                game_ids
            )
        ]

        if not relevant.empty:
            chunks.append(relevant)

    if not chunks:
        return pd.DataFrame()

    lineups = pd.concat(
        chunks,
        ignore_index=True,
    )
    lineups["season"] = lineups[
        "game_id"
    ].map(game_seasons)

    return lineups


def build_position_profiles(
    identities,
    lineups,
):
    current_starts = lineups[
        (lineups["season"] == CURRENT_SEASON)
        & (lineups["type"] == "starting_lineup")
        & lineups["position"].notna()
    ].copy()
    current_starts["mapped_position"] = (
        current_starts["position"].map(
            POSITION_MAP
        )
    )
    current_starts = current_starts[
        current_starts["mapped_position"]
        .notna()
    ]

    counts = (
        current_starts.groupby(
            [
                "player_id",
                "mapped_position",
            ]
        )
        .size()
        .reset_index(name="starts")
        .sort_values(
            ["player_id", "starts"],
            ascending=[True, False],
        )
    )

    lineup_positions = {}

    for player_id, group in counts.groupby(
        "player_id"
    ):
        records = group.to_dict(
            orient="records"
        )
        total = sum(
            record["starts"]
            for record in records
        )
        primary = records[0]
        secondary = None

        if len(records) > 1:
            candidate = records[1]
            if (
                candidate["starts"] >= 2
                and candidate["starts"] / total
                >= 0.15
            ):
                secondary = candidate

        lineup_positions[int(player_id)] = {
            "primary": primary[
                "mapped_position"
            ],
            "secondary": (
                None
                if secondary is None
                else secondary[
                    "mapped_position"
                ]
            ),
            "starts": int(total),
            "primary_share": round(
                primary["starts"] / total * 100,
                1,
            ),
            "history": " | ".join(
                f"{record['mapped_position']}:"
                f"{record['starts']}"
                for record in records
            ),
        }

    rows = []

    for _, identity in identities.iterrows():
        transfermarkt_id = identity.get(
            "transfermarkt_player_id"
        )
        lineup_position = None

        if pd.notna(transfermarkt_id):
            lineup_position = lineup_positions.get(
                int(transfermarkt_id)
            )

        mapped_profile_position = POSITION_MAP.get(
            identity.get(
                "transfermarkt_position"
            )
        )

        if mapped_profile_position:
            primary = mapped_profile_position
            secondary = None

            if (
                lineup_position is not None
                and lineup_position["starts"] >= 3
            ):
                lineup_primary = lineup_position[
                    "primary"
                ]
                lineup_secondary = lineup_position[
                    "secondary"
                ]

                if lineup_primary != primary:
                    secondary = lineup_primary
                elif lineup_secondary != primary:
                    secondary = lineup_secondary

                source = (
                    "transfermarkt_profile_and_lineups"
                )
                confidence = 95.0
            else:
                source = "transfermarkt_profile"
                confidence = 85.0

            # The Transfermarkt profile is the canonical
            # position. Formation labels such as LM/RM can
            # describe a wing-back's match role, so they are
            # useful as a secondary position but must not
            # outweigh the canonical profile in role matching.
            history = ""
        elif (
            lineup_position is not None
            and lineup_position["starts"] >= 3
        ):
            primary = lineup_position["primary"]
            secondary = lineup_position[
                "secondary"
            ]
            source = "transfermarkt_lineups"
            confidence = lineup_position[
                "primary_share"
            ]
            history = lineup_position["history"]
        else:
            primary = identity[
                "primary_position"
            ]
            secondary = identity.get(
                "secondary_position"
            )
            source = identity.get(
                "position_source",
                "transfit_fallback",
            )
            confidence = identity.get(
                "position_confidence",
                50.0,
            )
            history = identity.get(
                "position_history",
                "",
            )

        rows.append({
            "api_football_player_id": int(
                identity["player_id"]
            ),
            "verified_primary_position": primary,
            "verified_secondary_position": secondary,
            "verified_position_group": GROUP_MAP.get(
                primary,
                BROAD_GROUP_MAP.get(
                    identity.get("broad_position"),
                    "OTHER",
                ),
            ),
            "verified_position_source": source,
            "verified_position_confidence": confidence,
            "verified_position_history": history,
            "transfermarkt_position": identity.get(
                "transfermarkt_position"
            ),
        })

    return pd.DataFrame(rows)


def aggregate_seasons(
    appearances,
    lineups,
):
    season_stats = appearances.groupby(
        ["player_id", "season"],
        as_index=False,
    ).agg(
        appearances=("game_id", "nunique"),
        goals=("goals", "sum"),
        assists=("assists", "sum"),
        minutes=("minutes_played", "sum"),
        weighted_goals=("weighted_goals", "sum"),
        weighted_assists=("weighted_assists", "sum"),
        weighted_minutes=("weighted_minutes", "sum"),
    )

    starts = (
        lineups[
            lineups["type"]
            == "starting_lineup"
        ]
        .groupby(
            ["player_id", "season"],
            as_index=False,
        )
        .agg(starts=("game_id", "nunique"))
    )

    return season_stats.merge(
        starts,
        on=["player_id", "season"],
        how="left",
    ).fillna({"starts": 0})


def add_realism_scores(data):
    numeric_columns = [
        "current_appearances",
        "current_starts",
        "current_minutes",
        "current_goals",
        "current_assists",
        "current_weighted_goals",
        "current_weighted_assists",
        "current_weighted_minutes",
        "recent_weighted_output",
        "recent_weighted_minutes",
        "recent_starts",
    ]

    for column in numeric_columns:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
        ).fillna(0)

    data["current_weighted_output"] = (
        data["current_weighted_goals"]
        + data["current_weighted_assists"]
        * 0.70
    )
    data["current_output_per90"] = np.where(
        data["current_weighted_minutes"] > 0,
        data["current_weighted_output"]
        / data["current_weighted_minutes"]
        * 90,
        0,
    )

    data["current_output_percentile"] = 0.0
    data["current_rate_percentile"] = 0.0
    data["current_minutes_percentile"] = 0.0
    data["recent_output_percentile"] = 0.0
    data["recent_minutes_percentile"] = 0.0

    for _, indexes in data.groupby(
        "verified_position_group",
        dropna=False,
    ).groups.items():
        current_rate = data.loc[
            indexes,
            "current_output_per90",
        ]
        group_median = current_rate.median()
        reliability = (
            data.loc[
                indexes,
                "current_weighted_minutes",
            ]
            / 1800
        ).clip(0, 1)
        regressed_rate = (
            group_median
            + reliability
            * (current_rate - group_median)
        )

        data.loc[
            indexes,
            "current_output_percentile",
        ] = percentile(
            data.loc[
                indexes,
                "current_weighted_output",
            ]
        )
        data.loc[
            indexes,
            "current_rate_percentile",
        ] = percentile(regressed_rate)
        data.loc[
            indexes,
            "current_minutes_percentile",
        ] = percentile(
            data.loc[
                indexes,
                "current_weighted_minutes",
            ]
        )
        data.loc[
            indexes,
            "recent_output_percentile",
        ] = percentile(
            data.loc[
                indexes,
                "recent_weighted_output",
            ]
        )
        data.loc[
            indexes,
            "recent_minutes_percentile",
        ] = percentile(
            data.loc[
                indexes,
                "recent_weighted_minutes",
            ]
        )

    production_scores = []
    proven_scores = []

    for _, row in data.iterrows():
        group = row[
            "verified_position_group"
        ]

        if group in ATTACK_GROUPS:
            production = (
                row["current_output_percentile"]
                * 0.75
                + row["current_rate_percentile"]
                * 0.25
            )
            proven = (
                row["recent_output_percentile"]
                * 0.65
                + row["recent_minutes_percentile"]
                * 0.35
            )
        elif group in MIDFIELD_GROUPS:
            production = (
                row["current_output_percentile"]
                * 0.45
                + row["current_minutes_percentile"]
                * 0.55
            )
            proven = (
                row["recent_output_percentile"]
                * 0.35
                + row["recent_minutes_percentile"]
                * 0.65
            )
        else:
            production = (
                row["current_output_percentile"]
                * 0.15
                + row["current_minutes_percentile"]
                * 0.85
            )
            proven = (
                row["recent_output_percentile"]
                * 0.15
                + row["recent_minutes_percentile"]
                * 0.85
            )

        production_scores.append(production)
        proven_scores.append(proven)

    data["production_score"] = production_scores
    data["proven_score"] = proven_scores

    minutes_score = (
        data["current_minutes"] / 2700 * 100
    ).clip(0, 100)
    starts_score = (
        data["current_starts"] / 30 * 100
    ).clip(0, 100)
    appearances_score = (
        data["current_appearances"] / 40 * 100
    ).clip(0, 100)

    data["availability_score"] = (
        minutes_score * 0.55
        + starts_score * 0.30
        + appearances_score * 0.15
    )

    data["market_value_m_eur"] = pd.to_numeric(
        data["market_value_m_eur"],
        errors="coerce",
    )
    data["market_validation_score"] = np.nan
    valid_market = data["market_value_m_eur"].notna()
    data.loc[
        valid_market,
        "market_validation_score",
    ] = (
        data[valid_market]
        .groupby("verified_position_group")[
            "market_value_m_eur"
        ]
        .rank(
            pct=True,
            method="average",
        )
        * 100
    )
    data["market_validation_score"] = pd.to_numeric(
        data["market_validation_score"],
        errors="coerce",
    )

    score_columns = [
        "current_output_percentile",
        "current_rate_percentile",
        "current_minutes_percentile",
        "recent_output_percentile",
        "recent_minutes_percentile",
        "production_score",
        "proven_score",
        "availability_score",
        "market_validation_score",
    ]
    data[score_columns] = data[
        score_columns
    ].clip(0, 100).round(1)

    return data


def build_profiles():
    identities = load_identity_data()
    transfermarkt_ids = set(
        identities[
            "transfermarkt_player_id"
        ].dropna().astype(int)
    )
    games = load_recent_games()
    appearances = load_relevant_appearances(
        transfermarkt_ids,
        games,
    )
    lineups = load_relevant_lineups(
        transfermarkt_ids,
        games,
    )
    positions = build_position_profiles(
        identities,
        lineups,
    )
    season_stats = aggregate_seasons(
        appearances,
        lineups,
    )

    current = season_stats[
        season_stats["season"]
        == CURRENT_SEASON
    ].copy()
    current = current.rename(columns={
        "player_id": "transfermarkt_player_id",
        "appearances": "current_appearances",
        "starts": "current_starts",
        "minutes": "current_minutes",
        "goals": "current_goals",
        "assists": "current_assists",
        "weighted_goals": "current_weighted_goals",
        "weighted_assists": "current_weighted_assists",
        "weighted_minutes": "current_weighted_minutes",
    })

    recent = season_stats.copy()
    recent["recency_weight"] = recent[
        "season"
    ].map(RECENT_SEASONS)
    recent["weighted_output"] = (
        recent["weighted_goals"]
        + recent["weighted_assists"] * 0.70
    ) * recent["recency_weight"]
    recent["weighted_minutes_recent"] = (
        recent["weighted_minutes"]
        * recent["recency_weight"]
    )
    recent["starts_recent"] = (
        recent["starts"]
        * recent["recency_weight"]
    )
    recent = recent.groupby(
        "player_id",
        as_index=False,
    ).agg(
        recent_weighted_output=(
            "weighted_output",
            "sum",
        ),
        recent_weighted_minutes=(
            "weighted_minutes_recent",
            "sum",
        ),
        recent_starts=(
            "starts_recent",
            "sum",
        ),
    ).rename(columns={
        "player_id": "transfermarkt_player_id"
    })

    output = identities[[
        "player_id",
        "name",
        "team",
        "league",
        "age",
        "transfermarkt_player_id",
        "contract_expiration_date",
        "market_value_m_eur",
    ]].rename(columns={
        "player_id": "api_football_player_id",
    }).merge(
        positions,
        on="api_football_player_id",
        how="left",
    ).merge(
        current.drop(
            columns=["season"],
            errors="ignore",
        ),
        on="transfermarkt_player_id",
        how="left",
    ).merge(
        recent,
        on="transfermarkt_player_id",
        how="left",
    )

    output = add_realism_scores(output)
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    output.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    coverage = (
        output["current_appearances"] > 0
    ).mean() * 100
    verified_positions = output[
        "verified_position_source"
    ].astype(str).str.startswith(
        "transfermarkt"
    ).mean() * 100

    print(
        f"Built {len(output):,} realism profiles."
    )
    print(
        f"Current-season all-competition coverage: "
        f"{coverage:.1f}%"
    )
    print(
        f"Transfermarkt-verified positions: "
        f"{verified_positions:.1f}%"
    )
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_profiles()
