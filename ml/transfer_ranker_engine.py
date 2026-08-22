"""Inference helpers for the pairwise club-role learning-to-rank model."""

import json
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from ml.ranker_config import PAIR_FEATURES, pair_record


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RANKER_MODEL_PATH = PROJECT_ROOT / "models/transfer_ranker_v1.joblib"
RANKER_METADATA_PATH = (
    PROJECT_ROOT / "models/transfer_ranker_v1_metadata.json"
)


@lru_cache(maxsize=1)
def load_ranker_bundle():
    if not RANKER_MODEL_PATH.exists():
        return None
    return joblib.load(RANKER_MODEL_PATH)


@lru_cache(maxsize=1)
def ranker_status():
    if not RANKER_MODEL_PATH.exists() or not RANKER_METADATA_PATH.exists():
        return {"available": False}
    metadata = json.loads(
        RANKER_METADATA_PATH.read_text(encoding="utf-8")
    )
    return {
        "available": True,
        "model_version": metadata.get("version"),
        "trained_at": metadata.get("trained_at"),
        "method": metadata.get("method"),
        "group_definition": metadata.get("group_definition"),
        "samples": metadata.get("samples"),
        "test_metrics": metadata.get("test_metrics"),
        "baseline_metrics": metadata.get("pointwise_baseline_metrics"),
        "combined_test_metrics": metadata.get("combined_test_metrics"),
        "recommended_blend": metadata.get("recommended_blend"),
        "feature_count": len(metadata.get("features", [])),
    }


def confidence_label(comparison_count, certainty):
    if comparison_count >= 8 and certainty >= 0.28:
        return "high"
    if comparison_count >= 4 and certainty >= 0.14:
        return "medium"
    return "low"


def rank_feature_rows(feature_rows):
    """Score each candidate by pairwise win probability in the live pool."""
    bundle = load_ranker_bundle()
    if bundle is None or len(feature_rows) < 2:
        return [None] * len(feature_rows)

    comparisons = []
    pair_indices = []
    for left_index, candidate_a in enumerate(feature_rows[:-1]):
        for right_index in range(left_index + 1, len(feature_rows)):
            comparisons.append(
                pair_record(candidate_a, feature_rows[right_index])
            )
            pair_indices.append((left_index, right_index))

    probabilities = bundle["model"].predict_proba(
        pd.DataFrame(comparisons, columns=PAIR_FEATURES)
    )[:, 1]
    wins = np.zeros(len(feature_rows), dtype=float)
    counts = np.zeros(len(feature_rows), dtype=float)
    certainty = np.zeros(len(feature_rows), dtype=float)

    for probability, (left_index, right_index) in zip(
        probabilities,
        pair_indices,
    ):
        wins[left_index] += probability
        wins[right_index] += 1.0 - probability
        counts[left_index] += 1.0
        counts[right_index] += 1.0
        pair_certainty = abs(float(probability) - 0.5) * 2.0
        certainty[left_index] += pair_certainty
        certainty[right_index] += pair_certainty

    results = []
    for index in range(len(feature_rows)):
        comparison_count = int(counts[index])
        mean_certainty = float(
            certainty[index] / max(counts[index], 1.0)
        )
        results.append({
            "model_version": bundle["version"],
            "club_role_rank_score": round(
                float(100.0 * wins[index] / max(counts[index], 1.0)),
                1,
            ),
            "comparisons": comparison_count,
            "mean_pair_certainty": round(mean_certainty, 3),
            "confidence": confidence_label(
                comparison_count,
                mean_certainty,
            ),
            "relative_to_live_pool": True,
            "historical_training": True,
        })
    return results
