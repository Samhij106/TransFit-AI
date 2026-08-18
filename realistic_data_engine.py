from pathlib import Path

import pandas as pd


REALISM_FILE = Path(
    "data/processed/player_realism_profiles_2025.csv"
)
MARKET_VALUES_FILE = Path(
    "data/processed/player_market_values_2025.csv"
)


# Goals and assists are a strong quality signal for forwards,
# but progressively less useful for deeper roles. These weights
# control how much all-competition output is allowed to influence
# the role-specific league performance model.
OUTPUT_CONTEXT_WEIGHTS = {
    "FW": 0.50,
    "W": 0.40,
    "AM": 0.35,
    "CM": 0.18,
    "DM": 0.10,
    "FB": 0.10,
    "CB": 0.05,
}


# Proven level combines current role quality, three-season
# evidence, and a modest Transfermarkt peer signal. The market
# signal is most useful in roles where public G/A data is a poor
# description of quality (CB, FB, DM and CM).
PROVEN_LEVEL_WEIGHTS = {
    "FW": (0.30, 0.50, 0.20),
    "W": (0.30, 0.50, 0.20),
    "AM": (0.35, 0.45, 0.20),
    "CM": (0.45, 0.25, 0.30),
    "DM": (0.55, 0.15, 0.30),
    "FB": (0.55, 0.15, 0.30),
    "CB": (0.55, 0.15, 0.30),
}


def add_market_validation(profiles):
    profiles = profiles.copy()

    if MARKET_VALUES_FILE.exists():
        market_values = pd.read_csv(
            MARKET_VALUES_FILE,
            usecols=[
                "api_football_player_id",
                "market_value_m_eur",
            ],
        ).rename(columns={
            "api_football_player_id": "player_id",
        })
        market_values["player_id"] = pd.to_numeric(
            market_values["player_id"],
            errors="coerce",
        )
        market_values["market_value_m_eur"] = pd.to_numeric(
            market_values["market_value_m_eur"],
            errors="coerce",
        )

        profiles = profiles.drop(
            columns=["market_value_m_eur"],
            errors="ignore",
        ).merge(
            market_values,
            on="player_id",
            how="left",
        )
    else:
        profiles["market_value_m_eur"] = pd.NA

    profiles["market_validation_score"] = pd.NA
    valid_market = profiles["market_value_m_eur"].notna()

    profiles.loc[
        valid_market,
        "market_validation_score",
    ] = (
        profiles[valid_market]
        .groupby("verified_position_group")[
            "market_value_m_eur"
        ]
        .rank(
            pct=True,
            method="average",
        )
        * 100
    )

    profiles["market_validation_score"] = pd.to_numeric(
        profiles["market_validation_score"],
        errors="coerce",
    ).round(1)

    return profiles


def load_realism_profiles():
    if not REALISM_FILE.exists():
        return pd.DataFrame()

    profiles = pd.read_csv(
        REALISM_FILE
    )
    profiles = profiles.rename(columns={
        "api_football_player_id": "player_id"
    })
    profiles["player_id"] = pd.to_numeric(
        profiles["player_id"],
        errors="coerce",
    )
    profiles = profiles[
        profiles["player_id"].notna()
    ].copy()
    profiles["player_id"] = profiles[
        "player_id"
    ].astype(int)

    return add_market_validation(profiles)


def find_realism_by_id(
    profiles,
    player_id,
):
    if profiles.empty:
        return None

    result = profiles[
        profiles["player_id"]
        == int(player_id)
    ]

    if len(result) != 1:
        return None

    return result.iloc[0]


def realism_scores(
    realism_player,
    performance_score,
    minutes,
):
    if realism_player is None:
        availability = min(
            max(float(minutes), 0)
            / 2700
            * 100,
            100,
        )

        return {
            "production_score": float(
                performance_score
            ),
            "raw_proven_score": float(
                performance_score
            ),
            "market_validation_score": None,
            "market_value_m_eur": None,
            "availability_score": round(
                availability,
                1,
            ),
            "current_appearances": None,
            "current_starts": None,
            "current_minutes": float(minutes),
            "current_goals": None,
            "current_assists": None,
            "verified_position_source": None,
            "data_source": "transfit_fallback",
        }

    def number(column, fallback=0.0):
        value = realism_player.get(
            column,
            fallback,
        )

        if pd.isna(value):
            return fallback

        return float(value)

    return {
        "production_score": number(
            "production_score",
            performance_score,
        ),
        "raw_proven_score": number(
            "proven_score",
            performance_score,
        ),
        "market_validation_score": (
            None
            if pd.isna(realism_player.get(
                "market_validation_score"
            ))
            else number("market_validation_score")
        ),
        "market_value_m_eur": (
            None
            if pd.isna(realism_player.get(
                "market_value_m_eur"
            ))
            else number("market_value_m_eur")
        ),
        "availability_score": number(
            "availability_score"
        ),
        "current_appearances": int(number(
            "current_appearances"
        )),
        "current_starts": int(number(
            "current_starts"
        )),
        "current_minutes": int(number(
            "current_minutes",
            minutes,
        )),
        "current_goals": int(number(
            "current_goals"
        )),
        "current_assists": int(number(
            "current_assists"
        )),
        "verified_position_source": (
            realism_player.get(
                "verified_position_source"
            )
        ),
        "data_source": (
            "transfermarkt_all_competitions"
        ),
    }


def blend_performance_score(
    league_performance_score,
    production_score,
    position_group=None,
):
    output_weight = OUTPUT_CONTEXT_WEIGHTS.get(
        str(position_group),
        0.25,
    )

    return round(
        float(league_performance_score)
        * (1 - output_weight)
        + float(production_score)
        * output_weight,
        1,
    )


def calibrate_proven_level(
    league_performance_score,
    raw_proven_score,
    market_validation_score=None,
    position_group=None,
):
    quality_weight, history_weight, market_weight = (
        PROVEN_LEVEL_WEIGHTS.get(
            str(position_group),
            (0.45, 0.35, 0.20),
        )
    )

    if market_validation_score is None:
        available_weight = quality_weight + history_weight
        quality_weight /= available_weight
        history_weight /= available_weight
        market_weight = 0

    score = (
        float(league_performance_score)
        * quality_weight
        + float(raw_proven_score)
        * history_weight
        + float(market_validation_score or 0)
        * market_weight
    )

    return round(
        max(0, min(100, score)),
        1,
    )
