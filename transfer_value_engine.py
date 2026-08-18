import csv
import math
from pathlib import Path


MODEL_VERSION = "transfit-value-v1"
TRANSFERMARKT_MODEL = "transfermarkt-community-weekly"
BUDGET_TOLERANCE = 0.15
MARKET_VALUES_PATH = Path(
    "data/processed/player_market_values_2025.csv"
)
_MARKET_VALUES_CACHE = {}
_MARKET_VALUES_MTIME = None


LEAGUE_MULTIPLIERS = {
    "Premier League": 1.15,
    "La Liga": 1.05,
    "Bundesliga": 1.00,
    "Serie A": 0.95,
    "Ligue 1": 0.90,
}


POSITION_MULTIPLIERS = {
    "FW": 1.08,
    "W": 1.08,
    "AM": 1.06,
    "CM": 1.00,
    "DM": 0.96,
    "FB": 0.94,
    "CB": 0.92,
}


def clamp(value, low, high):
    return max(low, min(high, value))


def age_multiplier(age):
    age = float(age)

    if age <= 19:
        return 1.30
    if age <= 22:
        return 1.25
    if age <= 25:
        return 1.15
    if age <= 28:
        return 1.00
    if age <= 30:
        return 0.82
    if age <= 32:
        return 0.62
    return 0.40


def round_to_half_million(value):
    return round(value * 2) / 2


def estimate_transfer_value(
    performance_score,
    potential_score,
    age,
    minutes,
    league,
    position_group,
    position_source=None,
):
    performance_score = clamp(
        float(performance_score),
        0,
        100,
    )
    potential_score = clamp(
        float(potential_score),
        0,
        100,
    )
    minutes = max(0, float(minutes))

    quality_score = (
        performance_score * 0.60
        + potential_score * 0.40
    )

    quality_curve = (
        quality_score / 100
    ) ** 3

    base_value = (
        0.75
        + quality_curve * 115
    )

    star_premium = (
        max(0, quality_score - 85) ** 2
        * 0.35
    )

    minutes_multiplier = (
        0.65
        + 0.35
        * min(minutes / 1800, 1)
    )
    league_multiplier = (
        LEAGUE_MULTIPLIERS.get(
            str(league),
            0.90,
        )
    )
    role_multiplier = (
        POSITION_MULTIPLIERS.get(
            str(position_group),
            0.95,
        )
    )
    development_multiplier = (
        age_multiplier(age)
    )

    estimated_value = (
        (base_value + star_premium)
        * minutes_multiplier
        * league_multiplier
        * role_multiplier
        * development_multiplier
    )

    estimated_value = round_to_half_million(
        clamp(
            estimated_value,
            0.5,
            200,
        )
    )

    if minutes >= 1500:
        confidence = "medium"
    else:
        confidence = "low"

    if position_source == "statistical_fallback":
        confidence = "low"

    return {
        "estimated_value_m_eur": estimated_value,
        "market_value_m_eur": estimated_value,
        "confidence": confidence,
        "model": MODEL_VERSION,
        "quality_score": round(
            quality_score,
            1,
        ),
        "value_source": "transfit_estimate",
        "value_source_label": "TransFit estimate",
        "value_source_url": None,
        "value_updated_at": None,
        "transfermarkt_player_id": None,
        "value_match_method": None,
        "is_model_estimate": True,
    }


def load_market_values():
    global _MARKET_VALUES_CACHE
    global _MARKET_VALUES_MTIME

    if not MARKET_VALUES_PATH.exists():
        return {}

    modified_at = (
        MARKET_VALUES_PATH.stat().st_mtime_ns
    )

    if modified_at == _MARKET_VALUES_MTIME:
        return _MARKET_VALUES_CACHE

    market_values = {}

    with MARKET_VALUES_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as source:
        for row in csv.DictReader(source):
            try:
                player_id = int(
                    row[
                        "api_football_player_id"
                    ]
                )
                value_millions = float(
                    row["market_value_m_eur"]
                )
                transfermarkt_id = int(
                    row[
                        "transfermarkt_player_id"
                    ]
                )
            except (
                KeyError,
                TypeError,
                ValueError,
            ):
                continue

            market_values[player_id] = {
                "estimated_value_m_eur": (
                    value_millions
                ),
                "market_value_m_eur": (
                    value_millions
                ),
                "confidence": row.get(
                    "match_confidence",
                    "high",
                ),
                "model": TRANSFERMARKT_MODEL,
                "quality_score": None,
                "value_source": "transfermarkt",
                "value_source_label": (
                    "Transfermarkt market value"
                ),
                "value_source_url": row.get(
                    "transfermarkt_url"
                ) or None,
                "value_updated_at": row.get(
                    "valuation_date"
                ) or None,
                "transfermarkt_player_id": (
                    transfermarkt_id
                ),
                "value_match_method": row.get(
                    "match_method"
                ) or None,
                "is_model_estimate": False,
            }

    _MARKET_VALUES_CACHE = market_values
    _MARKET_VALUES_MTIME = modified_at

    return _MARKET_VALUES_CACHE


def resolve_transfer_value(
    player_id,
    performance_score,
    potential_score,
    age,
    minutes,
    league,
    position_group,
    position_source=None,
):
    market_value = load_market_values().get(
        int(player_id)
    )

    if market_value is not None:
        return dict(market_value)

    return estimate_transfer_value(
        performance_score=performance_score,
        potential_score=potential_score,
        age=age,
        minutes=minutes,
        league=league,
        position_group=position_group,
        position_source=position_source,
    )


def assess_budget(
    estimated_value_m_eur,
    budget_millions=None,
):
    if budget_millions is None:
        return {
            "budget_status": "not_set",
            "budget_difference_m_eur": None,
            "maximum_with_tolerance_m_eur": None,
        }

    budget = float(budget_millions)

    if not math.isfinite(budget) or budget <= 0:
        raise ValueError(
            "Budget must be greater than zero."
        )

    maximum = budget * (
        1 + BUDGET_TOLERANCE
    )
    value = float(
        estimated_value_m_eur
    )

    if value <= budget:
        status = "within_budget"
    elif value <= maximum:
        status = "stretch"
    else:
        status = "over_budget"

    return {
        "budget_status": status,
        "budget_difference_m_eur": round(
            value - budget,
            1,
        ),
        "maximum_with_tolerance_m_eur": round(
            maximum,
            1,
        ),
    }
