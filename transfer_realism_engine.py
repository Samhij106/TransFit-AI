import math
import unicodedata
from functools import lru_cache
from pathlib import Path

import pandas as pd


MARKET_VALUES_FILE = Path(
    "data/processed/player_market_values_2025.csv"
)
MODEL_VERSION = "club-stature-v1"


def clamp(value, low=0, high=100):
    return max(low, min(high, value))


def normalize_club_name(value):
    text = unicodedata.normalize(
        "NFKD",
        str(value or ""),
    )
    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )
    return " ".join(text.lower().split())


@lru_cache(maxsize=1)
def load_club_stature_profiles():
    if not MARKET_VALUES_FILE.exists():
        return {}

    values = pd.read_csv(
        MARKET_VALUES_FILE,
        usecols=[
            "current_team",
            "market_value_m_eur",
        ],
    )
    values["market_value_m_eur"] = pd.to_numeric(
        values["market_value_m_eur"],
        errors="coerce",
    )
    values = values.dropna(
        subset=["current_team", "market_value_m_eur"]
    )
    grouped = values.groupby("current_team")[
        "market_value_m_eur"
    ].agg(["count", "sum", "median", "max"])
    grouped["stature_percentile"] = (
        grouped["sum"].rank(pct=True, method="average") * 100
    )

    profiles = {}

    for club, row in grouped.iterrows():
        total_value = float(row["sum"])
        top_value = float(row["max"])
        median_value = float(row["median"])
        signing_ceiling = min(
            250.0,
            max(
                12.0,
                top_value * 1.8,
                total_value * 0.28,
                median_value * 5.0,
            ),
        )
        profiles[normalize_club_name(club)] = {
            "club": str(club),
            "player_count": int(row["count"]),
            "squad_value_m_eur": round(total_value, 1),
            "median_value_m_eur": round(median_value, 1),
            "top_value_m_eur": round(top_value, 1),
            "stature_percentile": round(
                float(row["stature_percentile"]),
                1,
            ),
            "signing_ceiling_m_eur": round(signing_ceiling, 1),
        }

    return profiles


def find_club_stature(club_name):
    return load_club_stature_profiles().get(
        normalize_club_name(club_name)
    )


def assess_transfer_feasibility(
    target_team,
    current_team,
    player_value_m_eur,
    performance_score,
    proven_score,
):
    target = find_club_stature(target_team)
    source = find_club_stature(current_team)
    value = max(float(player_value_m_eur or 0), 0)
    performance = float(performance_score or 0)
    proven = float(proven_score or 0)
    player_level = performance * 0.55 + proven * 0.45

    if target is None:
        return {
            "model": MODEL_VERSION,
            "score": 60.0,
            "status": "uncertain",
            "eligible": True,
            "target_stature_percentile": None,
            "source_stature_percentile": (
                None if source is None
                else source["stature_percentile"]
            ),
            "realistic_signing_ceiling_m_eur": None,
            "reason": "Target-club market profile is incomplete.",
        }

    ceiling = target["signing_ceiling_m_eur"]
    target_total = target["squad_value_m_eur"]
    target_top = target["top_value_m_eur"]
    value_ratio = value / max(ceiling, 1)
    value_score = clamp(
        104 - max(value_ratio - 0.35, 0) * 72
    )
    club_path_score = 72.0
    source_total = None

    if source is not None:
        source_total = source["squad_value_m_eur"]
        stature_step = math.log2(
            max(target_total, 1) / max(source_total, 1)
        )
        club_path_score = clamp(72 + stature_step * 17)

    stature_score = clamp(
        45 + target["stature_percentile"] * 0.55
    )
    feasibility_score = (
        value_score * 0.52
        + club_path_score * 0.33
        + stature_score * 0.15
    )

    hard_reasons = []

    if value > ceiling * 1.25:
        hard_reasons.append(
            "The player's value is far above the club's realistic "
            "recruitment ceiling."
        )

    if value >= 80 and target_total < 300:
        hard_reasons.append(
            "The target club is not currently in the market tier for "
            "an established superstar."
        )

    if (
        source_total is not None
        and source_total > target_total * 3.5
        and value > max(target_top * 1.3, 20)
    ):
        hard_reasons.append(
            "This would be an extreme downward club-status move for "
            "the player."
        )

    if (
        source_total is not None
        and player_level >= 90
        and target_total < source_total * 0.40
    ):
        hard_reasons.append(
            "The player's proven level is incompatible with the "
            "target club's current sporting tier."
        )

    if (
        source_total is not None
        and source_total > target_total * 5
        and player_level >= 81.5
        and target["stature_percentile"] < 35
    ):
        hard_reasons.append(
            "An established player at a much larger club is unlikely "
            "to accept this sporting-status drop."
        )

    if feasibility_score < 55:
        hard_reasons.append(
            "The combined club-stature and market gap is too large."
        )

    eligible = not hard_reasons

    if not eligible:
        status = "unrealistic"
        feasibility_score = min(feasibility_score, 34.0)
        reason = hard_reasons[0]
    elif feasibility_score >= 75:
        status = "realistic"
        reason = "Club stature and market value support a realistic move."
    elif feasibility_score >= 55:
        status = "ambitious"
        reason = "The move is ambitious but remains within a plausible range."
    else:
        status = "unlikely"
        reason = "The move requires a significant club-status or market step."

    return {
        "model": MODEL_VERSION,
        "score": round(clamp(feasibility_score), 1),
        "status": status,
        "eligible": eligible,
        "target_stature_percentile": target[
            "stature_percentile"
        ],
        "source_stature_percentile": (
            None if source is None
            else source["stature_percentile"]
        ),
        "realistic_signing_ceiling_m_eur": ceiling,
        "reason": reason,
    }
