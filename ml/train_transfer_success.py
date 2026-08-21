import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    ndcg_score,
    r2_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from ml.model_config import (
    CATEGORICAL_FEATURES,
    FEATURES,
    MODEL_VERSION,
    NUMERIC_FEATURES,
    SUCCESS_THRESHOLD,
    TARGET,
    TRAIN_END,
    VALIDATION_END,
)


DEFAULT_DATASET = Path("data/ml/transfer_success_dataset.csv")
DEFAULT_MODEL = Path("models/transfer_success_v1.joblib")
DEFAULT_METADATA = Path(
    "models/transfer_success_v1_metadata.json"
)


SEARCH_SPACE = [
    {
        "learning_rate": 0.04,
        "max_leaf_nodes": 15,
        "min_samples_leaf": 25,
        "l2_regularization": 1.0,
    },
    {
        "learning_rate": 0.04,
        "max_leaf_nodes": 31,
        "min_samples_leaf": 30,
        "l2_regularization": 2.0,
    },
    {
        "learning_rate": 0.07,
        "max_leaf_nodes": 15,
        "min_samples_leaf": 30,
        "l2_regularization": 2.0,
    },
    {
        "learning_rate": 0.07,
        "max_leaf_nodes": 31,
        "min_samples_leaf": 40,
        "l2_regularization": 4.0,
    },
]


def dataset_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def preprocessor():
    numeric = Pipeline([
        (
            "imputer",
            SimpleImputer(strategy="median"),
        ),
    ])
    categorical = Pipeline([
        (
            "imputer",
            SimpleImputer(
                strategy="constant",
                fill_value="unknown",
            ),
        ),
        (
            "encoder",
            OneHotEncoder(
                handle_unknown="ignore",
                min_frequency=10,
                max_categories=96,
                sparse_output=False,
            ),
        ),
    ])
    return ColumnTransformer(
        [
            ("numeric", numeric, NUMERIC_FEATURES),
            (
                "categorical",
                categorical,
                CATEGORICAL_FEATURES,
            ),
        ],
        sparse_threshold=0,
    )


def build_model(parameters, loss="absolute_error", quantile=None):
    model_parameters = {
        "loss": loss,
        "max_iter": 350,
        "early_stopping": True,
        "validation_fraction": 0.12,
        "n_iter_no_change": 30,
        "random_state": 42,
        **parameters,
    }
    if quantile is not None:
        model_parameters["quantile"] = quantile

    return Pipeline([
        ("features", preprocessor()),
        (
            "model",
            HistGradientBoostingRegressor(
                **model_parameters
            ),
        ),
    ])


def ranking_ndcg(frame, predictions, minimum_group_size=3):
    evaluation = frame[
        ["ranking_group", TARGET]
    ].copy()
    evaluation["prediction"] = predictions
    scores = []

    for _, group in evaluation.groupby("ranking_group"):
        if len(group) < minimum_group_size:
            continue
        scores.append(
            ndcg_score(
                [group[TARGET].to_numpy()],
                [group["prediction"].to_numpy()],
                k=min(10, len(group)),
            )
        )

    if not scores:
        return None
    return float(np.mean(scores))


def metrics(frame, predictions):
    actual = frame[TARGET].to_numpy()
    clipped = np.clip(predictions, 0, 100)
    binary = (actual >= SUCCESS_THRESHOLD).astype(int)
    result = {
        "samples": int(len(frame)),
        "mae": float(mean_absolute_error(actual, clipped)),
        "rmse": float(
            mean_squared_error(actual, clipped) ** 0.5
        ),
        "r2": float(r2_score(actual, clipped)),
        "ndcg_at_10": ranking_ndcg(frame, clipped),
    }
    if len(np.unique(binary)) > 1:
        result["success_auc"] = float(
            roc_auc_score(binary, clipped)
        )
    return result


def rounded_metrics(values):
    return {
        key: (
            None
            if value is None
            else round(float(value), 5)
        )
        for key, value in values.items()
    }


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


def reference_values(dataset):
    numeric = {
        feature: float(
            pd.to_numeric(
                dataset[feature],
                errors="coerce",
            ).median()
        )
        for feature in NUMERIC_FEATURES
    }
    categorical = {}
    for feature in CATEGORICAL_FEATURES:
        mode = dataset[feature].dropna().astype(str).mode()
        categorical[feature] = (
            mode.iloc[0] if not mode.empty else "unknown"
        )
    return {
        "numeric": numeric,
        "categorical": categorical,
    }


def calibration_table(frame, predictions):
    calibration = pd.DataFrame({
        "actual": frame[TARGET].to_numpy(),
        "prediction": np.clip(predictions, 0, 100),
    })
    calibration["bucket"] = pd.qcut(
        calibration["prediction"],
        q=10,
        duplicates="drop",
    )
    grouped = calibration.groupby(
        "bucket",
        observed=True,
    ).agg(
        samples=("actual", "size"),
        predicted=("prediction", "mean"),
        actual=("actual", "mean"),
    )
    return [
        {
            "samples": int(row.samples),
            "predicted": round(float(row.predicted), 3),
            "actual": round(float(row.actual), 3),
        }
        for row in grouped.itertuples()
    ]


def train(dataset_path, model_path, metadata_path):
    dataset = pd.read_csv(dataset_path)
    dataset["to_club_id"] = (
        dataset["to_club_id"].astype("Int64").astype(str)
    )
    train_frame, validation_frame, test_frame = split_dataset(
        dataset
    )

    if min(
        len(train_frame),
        len(validation_frame),
        len(test_frame),
    ) == 0:
        raise ValueError(
            "Time split produced an empty train, validation or test set."
        )

    search_results = []
    best_parameters = None
    best_key = None

    for parameters in SEARCH_SPACE:
        candidate = build_model(parameters)
        candidate.fit(
            train_frame[FEATURES],
            train_frame[TARGET],
        )
        predictions = candidate.predict(
            validation_frame[FEATURES]
        )
        evaluation = metrics(validation_frame, predictions)
        key = (
            evaluation["mae"],
            -float(evaluation["ndcg_at_10"] or 0),
        )
        search_results.append({
            "parameters": parameters,
            "metrics": rounded_metrics(evaluation),
        })
        if best_key is None or key < best_key:
            best_key = key
            best_parameters = parameters

    development = pd.concat(
        [train_frame, validation_frame],
        ignore_index=True,
    )
    central_model = build_model(best_parameters)
    lower_model = build_model(
        best_parameters,
        loss="quantile",
        quantile=0.10,
    )
    upper_model = build_model(
        best_parameters,
        loss="quantile",
        quantile=0.90,
    )

    for model in (central_model, lower_model, upper_model):
        model.fit(development[FEATURES], development[TARGET])

    development_predictions = np.clip(
        central_model.predict(development[FEATURES]),
        0,
        100,
    )
    percentile_grid = np.linspace(0, 1, 101)
    prediction_quantiles = np.quantile(
        development_predictions,
        percentile_grid,
    ).tolist()

    test_predictions = central_model.predict(test_frame[FEATURES])
    lower_predictions = lower_model.predict(test_frame[FEATURES])
    upper_predictions = upper_model.predict(test_frame[FEATURES])
    test_metrics = metrics(test_frame, test_predictions)
    interval_coverage = np.mean(
        (test_frame[TARGET].to_numpy() >= lower_predictions)
        & (test_frame[TARGET].to_numpy() <= upper_predictions)
    )

    baseline_prediction = np.repeat(
        development[TARGET].median(),
        len(test_frame),
    )
    baseline_metrics = metrics(test_frame, baseline_prediction)

    importance_sample = test_frame.sample(
        n=min(2500, len(test_frame)),
        random_state=42,
    )
    importance = permutation_importance(
        central_model,
        importance_sample[FEATURES],
        importance_sample[TARGET],
        scoring="neg_mean_absolute_error",
        n_repeats=3,
        random_state=42,
        n_jobs=-1,
    )
    feature_importance = sorted(
        [
            {
                "feature": feature,
                "importance": round(float(score), 6),
            }
            for feature, score in zip(
                FEATURES,
                importance.importances_mean,
            )
        ],
        key=lambda item: item["importance"],
        reverse=True,
    )

    bundle = {
        "version": MODEL_VERSION,
        "model": central_model,
        "lower_model": lower_model,
        "upper_model": upper_model,
        "features": FEATURES,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "reference_values": reference_values(development),
        "prediction_quantiles": prediction_quantiles,
        "success_threshold": SUCCESS_THRESHOLD,
    }
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, model_path, compress=3)

    metadata = {
        "version": MODEL_VERSION,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset_sha256": dataset_hash(dataset_path),
        "date_split": {
            "train_end": TRAIN_END,
            "validation_end": VALIDATION_END,
        },
        "samples": {
            "train": int(len(train_frame)),
            "validation": int(len(validation_frame)),
            "test": int(len(test_frame)),
        },
        "target": TARGET,
        "features": FEATURES,
        "selected_parameters": best_parameters,
        "validation_search": search_results,
        "test_metrics": rounded_metrics(test_metrics),
        "baseline_metrics": rounded_metrics(baseline_metrics),
        "prediction_interval_coverage": round(
            float(interval_coverage),
            5,
        ),
        "prediction_quantiles": [
            round(float(value), 5)
            for value in prediction_quantiles
        ],
        "calibration": calibration_table(
            test_frame,
            test_predictions,
        ),
        "feature_importance": feature_importance,
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )
    return metadata


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Train and evaluate the TransFit historical transfer "
            "success model."
        )
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET,
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=DEFAULT_MODEL,
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=DEFAULT_METADATA,
    )
    args = parser.parse_args()

    if not args.dataset.exists():
        raise SystemExit(f"Training dataset not found: {args.dataset}")

    metadata = train(
        args.dataset,
        args.model,
        args.metadata,
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
