import json
import math
import unicodedata
from datetime import date
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from ml.model_config import FEATURES, LEAGUE_STRENGTH
from ml.transfer_ranker_engine import rank_feature_rows, ranker_status


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models/transfer_success_v1.joblib"
MODEL_METADATA_PATH = (
    PROJECT_ROOT / "models/transfer_success_v1_metadata.json"
)
PLAYER_CONTEXT_PATH = (
    PROJECT_ROOT / "data/processed/ml_player_context_2025.csv"
)
CLUB_CONTEXT_PATH = (
    PROJECT_ROOT / "data/processed/ml_club_context_2025.csv"
)
CLUB_ALIASES_PATH = (
    PROJECT_ROOT / "data/processed/ml_club_aliases_2025.csv"
)

HYBRID_EXPERT_WEIGHT = 0.70
HYBRID_ML_WEIGHT = 0.30
HYBRID_SUCCESS_WEIGHT = 0.285
HYBRID_RANKER_WEIGHT = 0.015
HYBRID_SCORE_VERSION = "TransFit V11 Dual-ML Ranking"

LEAGUE_TO_COMPETITION = {
    "premier league": "GB1",
    "la liga": "ES1",
    "serie a": "IT1",
    "bundesliga": "L1",
    "ligue 1": "FR1",
}


def normalize_text(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )
    return " ".join(text.lower().split())


def finite_number(value, default=0.0):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float(default)
    return number if math.isfinite(number) else float(default)


def optional_integer(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return int(number)


def optional_text(value):
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


@lru_cache(maxsize=1)
def load_model_bundle():
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)


@lru_cache(maxsize=1)
def model_status():
    if not MODEL_PATH.exists() or not MODEL_METADATA_PATH.exists():
        return {
            "available": False,
            "hybrid_version": HYBRID_SCORE_VERSION,
            "learning_to_rank": ranker_status(),
        }

    metadata = json.loads(
        MODEL_METADATA_PATH.read_text(encoding="utf-8")
    )
    return {
        "available": True,
        "hybrid_version": HYBRID_SCORE_VERSION,
        "model_version": metadata.get("version"),
        "trained_at": metadata.get("trained_at"),
        "samples": metadata.get("samples"),
        "test_metrics": metadata.get("test_metrics"),
        "baseline_metrics": metadata.get("baseline_metrics"),
        "prediction_interval_coverage": metadata.get(
            "prediction_interval_coverage"
        ),
        "feature_count": len(metadata.get("features", [])),
        "top_features": metadata.get("feature_importance", [])[:8],
        "learning_to_rank": ranker_status(),
    }


@lru_cache(maxsize=1)
def load_inference_context():
    if not all(path.exists() for path in (
        PLAYER_CONTEXT_PATH,
        CLUB_CONTEXT_PATH,
        CLUB_ALIASES_PATH,
    )):
        return None

    players = pd.read_csv(PLAYER_CONTEXT_PATH)
    clubs = pd.read_csv(CLUB_CONTEXT_PATH)
    aliases = pd.read_csv(CLUB_ALIASES_PATH)

    player_by_transfermarkt_id = {}
    for _, player in players.iterrows():
        player_id = optional_integer(
            player.get("transfermarkt_player_id")
        )
        if player_id is not None:
            player_by_transfermarkt_id[player_id] = player

    club_by_id = {}
    for _, club in clubs.iterrows():
        club_id = optional_integer(club.get("club_id"))
        if club_id is not None:
            club_by_id[club_id] = club

    club_id_by_alias = {}
    for _, alias in aliases.iterrows():
        club_id = optional_integer(alias.get("current_club_id"))
        if club_id is not None:
            club_id_by_alias[normalize_text(alias.get("alias"))] = club_id

    return {
        "players": player_by_transfermarkt_id,
        "clubs": club_by_id,
        "aliases": club_id_by_alias,
    }


def club_for_name(context, club_name):
    club_id = context["aliases"].get(normalize_text(club_name))
    if club_id is None:
        return None
    return context["clubs"].get(club_id)


def competition_from_league(league):
    return LEAGUE_TO_COMPETITION.get(normalize_text(league))


def build_feature_row(
    *,
    transfermarkt_player_id,
    current_team,
    target_team,
    current_league,
    target_league,
    age,
    market_value_m_eur,
    appearances,
    starts,
    minutes,
    goals,
    assists,
    primary_position=None,
):
    bundle = load_model_bundle()
    context = load_inference_context()
    transfermarkt_id = optional_integer(transfermarkt_player_id)

    if bundle is None or context is None or transfermarkt_id is None:
        return None

    player = context["players"].get(transfermarkt_id)
    if player is None:
        return None

    source_club_id = optional_integer(player.get("current_club_id"))
    source_club = context["clubs"].get(source_club_id)
    target_club = club_for_name(context, target_team)
    if target_club is None:
        return None

    source_competition = (
        None
        if source_club is None
        else source_club.get("domestic_competition_id")
    )
    if not source_competition or pd.isna(source_competition):
        source_competition = competition_from_league(current_league)

    target_competition = target_club.get(
        "domestic_competition_id"
    )
    if not target_competition or pd.isna(target_competition):
        target_competition = competition_from_league(target_league)

    appearances = finite_number(appearances)
    starts = finite_number(starts)
    minutes = finite_number(minutes)
    goals = finite_number(goals)
    assists = finite_number(assists)
    source_games = finite_number(
        None if source_club is None
        else source_club.get("games_analyzed")
    )

    row = {
        "age_at_transfer": finite_number(age),
        "market_value_m_eur": finite_number(
            market_value_m_eur,
            player.get("recent_market_value_m_eur", 0),
        ),
        "market_value_trend_180d_pct": finite_number(
            player.get("market_value_trend_180d_pct")
        ),
        "pre_appearances": appearances,
        "pre_starts": starts,
        "pre_minutes": minutes,
        "pre_goals": goals,
        "pre_assists": assists,
        "pre_goal_assist_per90": (
            90.0 * (goals + assists) / minutes
            if minutes > 0
            else 0.0
        ),
        "pre_minutes_share": min(
            minutes / max(source_games * 90.0, 1.0),
            1.0,
        ),
        "pre_start_share": min(
            starts / max(source_games, 1.0),
            1.0,
        ),
        "from_points_per_game": finite_number(
            None if source_club is None
            else source_club.get("points_per_game")
        ),
        "to_points_per_game": finite_number(
            target_club.get("points_per_game")
        ),
        "from_goal_difference_per_game": finite_number(
            None if source_club is None
            else source_club.get("goal_difference_per_game")
        ),
        "to_goal_difference_per_game": finite_number(
            target_club.get("goal_difference_per_game")
        ),
        "league_strength_gap": (
            LEAGUE_STRENGTH.get(str(target_competition), 60.0)
            - LEAGUE_STRENGTH.get(str(source_competition), 60.0)
        ),
        "previous_transfers_3y": finite_number(
            player.get("previous_transfers_3y")
        ),
        "is_cross_border": int(
            str(source_competition) != str(target_competition)
        ),
        "is_winter_window": int(date.today().month in (1, 2)),
        "broad_position": (
            optional_text(player.get("broad_position"))
            or optional_text(primary_position)
            or "Unknown"
        ),
        "sub_position": (
            optional_text(player.get("sub_position"))
            or optional_text(primary_position)
            or "Unknown"
        ),
        "from_competition_id": str(
            source_competition or "unknown"
        ),
        "to_competition_id": str(
            target_competition or "unknown"
        ),
        "to_club_id": str(int(target_club["club_id"])),
    }
    return {feature: row.get(feature) for feature in FEATURES}


def forecast_percentile(bundle, forecast):
    quantiles = np.asarray(
        bundle.get("prediction_quantiles", []),
        dtype=float,
    )
    if quantiles.size < 2:
        return None
    percentile = np.searchsorted(
        quantiles,
        forecast,
        side="right",
    ) / quantiles.size * 100
    return float(np.clip(percentile, 0, 100))


def local_feature_effects(bundle, feature_row, forecast):
    references = bundle.get("reference_values", {})
    numeric_references = references.get("numeric", {})
    categorical_references = references.get("categorical", {})
    perturbed_rows = []

    for feature in FEATURES:
        perturbed = dict(feature_row)
        if feature in numeric_references:
            perturbed[feature] = numeric_references[feature]
        else:
            perturbed[feature] = categorical_references.get(
                feature,
                "unknown",
            )
        perturbed_rows.append(perturbed)

    frame = pd.DataFrame(perturbed_rows, columns=FEATURES)
    counterfactuals = np.clip(
        bundle["model"].predict(frame),
        0,
        100,
    )
    effects = [
        {
            "feature": feature,
            "effect": round(float(forecast - counterfactual), 2),
        }
        for feature, counterfactual in zip(
            FEATURES,
            counterfactuals,
        )
    ]
    positive = sorted(
        (item for item in effects if item["effect"] > 0),
        key=lambda item: item["effect"],
        reverse=True,
    )[:4]
    negative = sorted(
        (item for item in effects if item["effect"] < 0),
        key=lambda item: item["effect"],
    )[:4]
    return {
        "method": "one-feature reference counterfactual",
        "reference": "training-development median or mode",
        "positive_drivers": positive,
        "risk_drivers": negative,
        "is_causal": False,
    }


def predict_feature_rows(feature_rows, include_explanations=False):
    bundle = load_model_bundle()
    if bundle is None or not feature_rows:
        return []

    frame = pd.DataFrame(feature_rows, columns=FEATURES)
    forecasts = np.clip(
        bundle["model"].predict(frame),
        0,
        100,
    )
    lowers = np.clip(
        bundle["lower_model"].predict(frame),
        0,
        100,
    )
    uppers = np.clip(
        bundle["upper_model"].predict(frame),
        0,
        100,
    )

    predictions = []
    for row, forecast, lower, upper in zip(
        feature_rows,
        forecasts,
        lowers,
        uppers,
    ):
        lower, upper = sorted((float(lower), float(upper)))
        interval_width = upper - lower
        confidence = (
            "high"
            if interval_width <= 25
            else "medium"
            if interval_width <= 42
            else "low"
        )
        percentile = forecast_percentile(bundle, float(forecast))
        prediction = {
            "model_version": bundle["version"],
            "success_forecast": round(float(forecast), 1),
            "success_percentile": (
                None if percentile is None else round(percentile, 1)
            ),
            "prediction_interval": {
                "lower": round(lower, 1),
                "upper": round(upper, 1),
            },
            "confidence": confidence,
            "historical_training": True,
        }
        if include_explanations:
            prediction["local_explanation"] = local_feature_effects(
                bundle,
                row,
                float(forecast),
            )
        predictions.append(prediction)
    return predictions


def build_candidate_feature_rows(records, target_team, target_league):
    """Build model inputs while preserving candidate-list alignment."""
    aligned = [None] * len(records)

    for index, record in enumerate(records):
        all_competitions = record.get("all_competitions") or {}
        aligned[index] = build_feature_row(
            transfermarkt_player_id=record.get(
                "transfermarkt_player_id"
            ),
            current_team=record.get("current_team"),
            target_team=target_team,
            current_league=record.get("league"),
            target_league=target_league,
            age=record.get("age"),
            market_value_m_eur=record.get(
                "estimated_value_m_eur"
            ),
            appearances=all_competitions.get("appearances"),
            starts=all_competitions.get("starts"),
            minutes=all_competitions.get(
                "minutes",
                record.get("minutes"),
            ),
            goals=all_competitions.get("goals"),
            assists=all_competitions.get("assists"),
            primary_position=record.get("primary_position"),
        )
    return aligned


def predict_candidate_records(records, target_team, target_league):
    aligned_rows = build_candidate_feature_rows(
        records,
        target_team,
        target_league,
    )
    feature_rows = []
    valid_indices = []

    for index, row in enumerate(aligned_rows):
        if row is None:
            continue
        valid_indices.append(index)
        feature_rows.append(row)

    aligned = [None] * len(records)
    for index, prediction in zip(
        valid_indices,
        predict_feature_rows(feature_rows),
    ):
        aligned[index] = prediction
    return aligned


def predict_candidate_rank_records(records, target_team, target_league):
    """Return pairwise club-role rank evidence aligned to live candidates."""
    aligned_rows = build_candidate_feature_rows(
        records,
        target_team,
        target_league,
    )
    valid_indices = [
        index
        for index, row in enumerate(aligned_rows)
        if row is not None
    ]
    valid_rows = [aligned_rows[index] for index in valid_indices]
    aligned = [None] * len(records)
    for index, prediction in zip(
        valid_indices,
        rank_feature_rows(valid_rows),
    ):
        aligned[index] = prediction
    return aligned


def hybrid_weight_payload(ranker_prediction=None):
    if ranker_prediction is None:
        return {
            "expert_model": round(HYBRID_EXPERT_WEIGHT * 100, 1),
            "historical_ml": round(HYBRID_ML_WEIGHT * 100, 1),
            "club_role_ranker": 0.0,
        }
    return {
        "expert_model": round(HYBRID_EXPERT_WEIGHT * 100, 1),
        "historical_ml": round(HYBRID_SUCCESS_WEIGHT * 100, 1),
        "club_role_ranker": round(HYBRID_RANKER_WEIGHT * 100, 1),
    }


def hybrid_score(expert_score, ml_prediction, ranker_prediction=None):
    expert = finite_number(expert_score)
    if not ml_prediction:
        return round(expert, 1)
    percentile = finite_number(
        ml_prediction.get("success_percentile"),
        expert,
    )
    if ranker_prediction is None:
        return round(
            expert * HYBRID_EXPERT_WEIGHT
            + percentile * HYBRID_ML_WEIGHT,
            1,
        )
    rank_score = finite_number(
        ranker_prediction.get("club_role_rank_score"),
        percentile,
    )
    return round(
        expert * HYBRID_EXPERT_WEIGHT
        + percentile * HYBRID_SUCCESS_WEIGHT
        + rank_score * HYBRID_RANKER_WEIGHT,
        1,
    )
