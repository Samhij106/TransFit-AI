"""Train and evaluate TransFit's pairwise learning-to-rank model.

The training unit is a pair of historical transfers made by the same club,
in the same season and within the same broad positional family. The target
states which transfer produced the stronger 365-day outcome. Both pair
directions are included so the classifier learns a symmetric preference.
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, log_loss, ndcg_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from ml.model_config import (
    TARGET,
    TRAIN_END,
    VALIDATION_END,
)
from ml.ranker_config import (
    MIN_GROUP_SIZE,
    MIN_RELEVANCE_GAP,
    PAIR_CATEGORICAL_FEATURES,
    PAIR_FEATURES,
    PAIR_NUMERIC_FEATURES,
    RANKER_BLEND_WEIGHT,
    RANKER_MODEL_VERSION,
    pair_record,
    safe_number,
)


DEFAULT_DATASET = Path("data/ml/transfer_success_dataset.csv")
DEFAULT_SUCCESS_MODEL = Path("models/transfer_success_v1.joblib")
DEFAULT_MODEL = Path("models/transfer_ranker_v1.joblib")
DEFAULT_METADATA = Path("models/transfer_ranker_v1_metadata.json")

SEARCH_SPACE = [
    {
        "learning_rate": 0.04,
        "max_leaf_nodes": 15,
        "min_samples_leaf": 35,
        "l2_regularization": 2.0,
    },
    {
        "learning_rate": 0.06,
        "max_leaf_nodes": 23,
        "min_samples_leaf": 45,
        "l2_regularization": 4.0,
    },
    {
        "learning_rate": 0.08,
        "max_leaf_nodes": 31,
        "min_samples_leaf": 55,
        "l2_regularization": 6.0,
    },
]


def dataset_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def split_dataset(dataset):
    dates = pd.to_datetime(dataset["transfer_date"])
    train_end = pd.Timestamp(TRAIN_END)
    validation_end = pd.Timestamp(VALIDATION_END)
    train = dataset[dates <= train_end].copy()
    validation = dataset[
        (dates > train_end) & (dates <= validation_end)
    ].copy()
    test = dataset[dates > validation_end].copy()
    return train, validation, test


def pairwise_dataset(dataset, include_reverse=True):
    records = []
    labels = []
    weights = []
    group_columns = ["ranking_group", "broad_position"]

    for _, group in dataset.groupby(group_columns, dropna=False):
        if len(group) < MIN_GROUP_SIZE:
            continue
        rows = group.to_dict(orient="records")
        for left_index, candidate_a in enumerate(rows[:-1]):
            for candidate_b in rows[left_index + 1:]:
                target_a = safe_number(candidate_a.get(TARGET))
                target_b = safe_number(candidate_b.get(TARGET))
                gap = abs(target_a - target_b)
                if not np.isfinite(gap) or gap < MIN_RELEVANCE_GAP:
                    continue

                label = int(target_a > target_b)
                weight = float(np.clip(gap / 50.0, 0.25, 2.0))
                records.append(pair_record(candidate_a, candidate_b))
                labels.append(label)
                weights.append(weight)

                if include_reverse:
                    records.append(pair_record(candidate_b, candidate_a))
                    labels.append(1 - label)
                    weights.append(weight)

    return (
        pd.DataFrame(records, columns=PAIR_FEATURES),
        np.asarray(labels, dtype=int),
        np.asarray(weights, dtype=float),
    )


def preprocessor():
    numeric = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
    ])
    categorical = Pipeline([
        (
            "imputer",
            SimpleImputer(strategy="constant", fill_value="unknown"),
        ),
        (
            "encoder",
            OneHotEncoder(
                handle_unknown="ignore",
                min_frequency=8,
                max_categories=96,
                sparse_output=False,
            ),
        ),
    ])
    return ColumnTransformer(
        [
            ("numeric", numeric, PAIR_NUMERIC_FEATURES),
            (
                "categorical",
                categorical,
                PAIR_CATEGORICAL_FEATURES,
            ),
        ],
        sparse_threshold=0,
    )


def build_model(parameters):
    return Pipeline([
        ("features", preprocessor()),
        (
            "model",
            HistGradientBoostingClassifier(
                loss="log_loss",
                max_iter=300,
                early_stopping=True,
                validation_fraction=0.12,
                n_iter_no_change=25,
                random_state=42,
                **parameters,
            ),
        ),
    ])


def group_rank_scores(model, dataset):
    scores = pd.Series(np.nan, index=dataset.index, dtype=float)
    group_columns = ["ranking_group", "broad_position"]

    for _, group in dataset.groupby(group_columns, dropna=False):
        if len(group) < MIN_GROUP_SIZE:
            continue
        rows = group.to_dict(orient="records")
        comparisons = []
        pair_indices = []
        for left_index, candidate_a in enumerate(rows[:-1]):
            for right_index in range(left_index + 1, len(rows)):
                comparisons.append(
                    pair_record(candidate_a, rows[right_index])
                )
                pair_indices.append((left_index, right_index))

        probabilities = model.predict_proba(
            pd.DataFrame(comparisons, columns=PAIR_FEATURES)
        )[:, 1]
        wins = np.zeros(len(rows), dtype=float)
        counts = np.zeros(len(rows), dtype=float)
        for probability, (left_index, right_index) in zip(
            probabilities,
            pair_indices,
        ):
            wins[left_index] += probability
            wins[right_index] += 1.0 - probability
            counts[left_index] += 1.0
            counts[right_index] += 1.0

        group_scores = 100.0 * wins / np.maximum(counts, 1.0)
        scores.loc[group.index] = group_scores

    return scores


def ranking_metrics(dataset, scores):
    evaluation = dataset[["ranking_group", "broad_position", TARGET]].copy()
    evaluation["rank_score"] = scores
    ndcg_values = []
    top_choice_outcomes = []
    top_possible_outcomes = []

    for _, group in evaluation.dropna(subset=["rank_score"]).groupby(
        ["ranking_group", "broad_position"],
        dropna=False,
    ):
        if len(group) < MIN_GROUP_SIZE:
            continue
        ndcg_values.append(ndcg_score(
            [group[TARGET].to_numpy()],
            [group["rank_score"].to_numpy()],
            k=min(10, len(group)),
        ))
        top_index = group["rank_score"].idxmax()
        top_choice_outcomes.append(float(group.loc[top_index, TARGET]))
        top_possible_outcomes.append(float(group[TARGET].max()))

    return {
        "groups": len(ndcg_values),
        "ndcg_at_10": (
            None if not ndcg_values else float(np.mean(ndcg_values))
        ),
        "mean_top_choice_success": (
            None
            if not top_choice_outcomes
            else float(np.mean(top_choice_outcomes))
        ),
        "mean_best_available_success": (
            None
            if not top_possible_outcomes
            else float(np.mean(top_possible_outcomes))
        ),
    }


def pointwise_baseline_scores(success_model_path, dataset):
    bundle = joblib.load(success_model_path)
    return np.clip(
        bundle["model"].predict(dataset[bundle["features"]]),
        0,
        100,
    )


def rounded_metrics(metrics):
    return {
        key: (
            int(value)
            if key == "groups"
            else None
            if value is None
            else round(float(value), 5)
        )
        for key, value in metrics.items()
    }


def train(dataset_path, success_model_path, model_path, metadata_path):
    dataset = pd.read_csv(dataset_path)
    train_frame, validation_frame, test_frame = split_dataset(dataset)

    train_pairs, train_labels, train_weights = pairwise_dataset(train_frame)
    validation_pairs, validation_labels, _ = pairwise_dataset(
        validation_frame
    )

    search_results = []
    best_parameters = None
    best_ndcg = -np.inf
    for parameters in SEARCH_SPACE:
        model = build_model(parameters)
        model.fit(
            train_pairs,
            train_labels,
            model__sample_weight=train_weights,
        )
        probabilities = model.predict_proba(validation_pairs)[:, 1]
        rank_scores = group_rank_scores(model, validation_frame)
        rank_metrics = ranking_metrics(validation_frame, rank_scores)
        result = {
            "parameters": parameters,
            "pairwise_auc": float(
                roc_auc_score(validation_labels, probabilities)
            ),
            "pairwise_accuracy": float(
                accuracy_score(
                    validation_labels,
                    probabilities >= 0.5,
                )
            ),
            "pairwise_log_loss": float(
                log_loss(validation_labels, probabilities)
            ),
            **rank_metrics,
        }
        search_results.append(result)
        if rank_metrics["ndcg_at_10"] > best_ndcg:
            best_ndcg = rank_metrics["ndcg_at_10"]
            best_parameters = parameters

    development = pd.concat(
        [train_frame, validation_frame],
        ignore_index=True,
    )
    development_pairs, development_labels, development_weights = (
        pairwise_dataset(development)
    )
    final_model = build_model(best_parameters)
    final_model.fit(
        development_pairs,
        development_labels,
        model__sample_weight=development_weights,
    )

    test_pairs, test_labels, _ = pairwise_dataset(test_frame)
    test_probabilities = final_model.predict_proba(test_pairs)[:, 1]
    test_scores = group_rank_scores(final_model, test_frame)
    test_metrics = {
        "pairs": int(len(test_pairs)),
        "pairwise_auc": float(
            roc_auc_score(test_labels, test_probabilities)
        ),
        "pairwise_accuracy": float(
            accuracy_score(test_labels, test_probabilities >= 0.5)
        ),
        "pairwise_log_loss": float(
            log_loss(test_labels, test_probabilities)
        ),
        **ranking_metrics(test_frame, test_scores),
    }

    baseline_scores = pointwise_baseline_scores(
        success_model_path,
        test_frame,
    )
    baseline_metrics = ranking_metrics(test_frame, baseline_scores)
    combined_scores = (
        baseline_scores * (1.0 - RANKER_BLEND_WEIGHT)
        + test_scores * RANKER_BLEND_WEIGHT
    )
    combined_metrics = ranking_metrics(test_frame, combined_scores)

    bundle = {
        "version": RANKER_MODEL_VERSION,
        "model": final_model,
        "pair_features": PAIR_FEATURES,
        "numeric_features": PAIR_NUMERIC_FEATURES,
        "categorical_features": PAIR_CATEGORICAL_FEATURES,
        "minimum_relevance_gap": MIN_RELEVANCE_GAP,
        "recommended_blend": {
            "historical_success_model": round(
                1.0 - RANKER_BLEND_WEIGHT,
                3,
            ),
            "club_role_ranker": RANKER_BLEND_WEIGHT,
            "policy": (
                "conservative cap with a small held-out lift; "
                "larger weights were unstable across time splits"
            ),
        },
    }
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, model_path, compress=3)

    metadata = {
        "version": RANKER_MODEL_VERSION,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset_sha256": dataset_hash(dataset_path),
        "method": "pairwise learning-to-rank",
        "group_definition": (
            "destination club + transfer season + broad position"
        ),
        "minimum_relevance_gap": MIN_RELEVANCE_GAP,
        "recommended_blend": bundle["recommended_blend"],
        "date_split": {
            "train_end": TRAIN_END,
            "validation_end": VALIDATION_END,
        },
        "samples": {
            "train_transfers": int(len(train_frame)),
            "validation_transfers": int(len(validation_frame)),
            "test_transfers": int(len(test_frame)),
            "development_pairs": int(len(development_pairs)),
            "test_pairs": int(len(test_pairs)),
        },
        "features": PAIR_FEATURES,
        "selected_parameters": best_parameters,
        "validation_search": [
            {
                key: (
                    value
                    if key == "parameters"
                    else round(float(value), 5)
                    if value is not None
                    else None
                )
                for key, value in result.items()
            }
            for result in search_results
        ],
        "test_metrics": rounded_metrics(test_metrics),
        "pointwise_baseline_metrics": rounded_metrics(
            baseline_metrics
        ),
        "combined_test_metrics": rounded_metrics(combined_metrics),
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )
    return metadata


def main():
    parser = argparse.ArgumentParser(
        description="Train TransFit's pairwise transfer ranker."
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument(
        "--success-model",
        type=Path,
        default=DEFAULT_SUCCESS_MODEL,
    )
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument(
        "--metadata",
        type=Path,
        default=DEFAULT_METADATA,
    )
    args = parser.parse_args()

    for required_path in (args.dataset, args.success_model):
        if not required_path.exists():
            raise SystemExit(f"Required artifact not found: {required_path}")

    metadata = train(
        args.dataset,
        args.success_model,
        args.model,
        args.metadata,
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
