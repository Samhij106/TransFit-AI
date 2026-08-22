"""Configuration and feature building for the club-role ranker."""

import numpy as np
import pandas as pd

from ml.model_config import NUMERIC_FEATURES


RANKER_MODEL_VERSION = "transfer-ranker-pairwise-hgb-v1"
RANKER_BLEND_WEIGHT = 0.05

MIN_RELEVANCE_GAP = 8.0
MIN_GROUP_SIZE = 2

PAIR_NUMERIC_FEATURES = [
    f"delta_{feature}"
    for feature in NUMERIC_FEATURES
] + [
    "target_points_per_game",
    "target_goal_difference_per_game",
    "same_sub_position",
    "same_source_league",
]

PAIR_CATEGORICAL_FEATURES = [
    "candidate_a_broad_position",
    "candidate_b_broad_position",
    "candidate_a_sub_position",
    "candidate_b_sub_position",
    "candidate_a_source_league",
    "candidate_b_source_league",
    "target_league",
    "target_club_id",
]

PAIR_FEATURES = PAIR_NUMERIC_FEATURES + PAIR_CATEGORICAL_FEATURES


def safe_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return np.nan
    return number if np.isfinite(number) else np.nan


def safe_category(value):
    if value is None or pd.isna(value):
        return "unknown"
    text = str(value).strip()
    return text or "unknown"


def pair_record(candidate_a, candidate_b):
    """Build one directional A-vs-B model input without outcome data."""
    record = {
        f"delta_{feature}": (
            safe_number(candidate_a.get(feature))
            - safe_number(candidate_b.get(feature))
        )
        for feature in NUMERIC_FEATURES
    }
    sub_a = safe_category(candidate_a.get("sub_position"))
    sub_b = safe_category(candidate_b.get("sub_position"))
    source_a = safe_category(
        candidate_a.get("from_competition_id")
    )
    source_b = safe_category(
        candidate_b.get("from_competition_id")
    )
    record.update({
        "target_points_per_game": safe_number(
            candidate_a.get("to_points_per_game")
        ),
        "target_goal_difference_per_game": safe_number(
            candidate_a.get("to_goal_difference_per_game")
        ),
        "same_sub_position": int(sub_a == sub_b),
        "same_source_league": int(source_a == source_b),
        "candidate_a_broad_position": safe_category(
            candidate_a.get("broad_position")
        ),
        "candidate_b_broad_position": safe_category(
            candidate_b.get("broad_position")
        ),
        "candidate_a_sub_position": sub_a,
        "candidate_b_sub_position": sub_b,
        "candidate_a_source_league": source_a,
        "candidate_b_source_league": source_b,
        "target_league": safe_category(
            candidate_a.get("to_competition_id")
        ),
        "target_club_id": safe_category(
            candidate_a.get("to_club_id")
        ),
    })
    return {feature: record.get(feature) for feature in PAIR_FEATURES}
