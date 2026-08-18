from pathlib import Path

import pandas as pd


REALISM_FILE = Path(
    "data/processed/player_realism_profiles_2025.csv"
)


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

    return profiles


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
            "proven_score": float(
                performance_score
            ),
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
        "proven_score": number(
            "proven_score",
            performance_score,
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
):
    return round(
        float(league_performance_score)
        * 0.55
        + float(production_score)
        * 0.45,
        1,
    )
