"""Audit the player-analysis dataset for invalid and suspicious outliers.

The audit separates hard data errors from statistical review candidates.
Extreme football performance can be legitimate, so robust outliers are never
silently removed.  Percentage metrics with tiny samples are reported because
they require sample-aware modelling.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_PLAYER_FILE = Path(
    "data/processed/player_profiles_season_2025.csv"
)
DEFAULT_TACTICAL_FILE = Path(
    "data/processed/player_tactical_profiles_2025.csv"
)

HARD_BOUNDS = {
    "age": (15, 50),
    "rating": (0, 10),
    "shot_accuracy": (0, 100),
    "dribble_success_rate": (0, 100),
    "pass_accuracy": (0, 100),
    "goals_per90": (0, None),
    "assists_per90": (0, None),
    "shots_per90": (0, None),
    "shots_on_target_per90": (0, None),
    "key_passes_per90": (0, None),
    "tackles_per90": (0, None),
    "interceptions_per90": (0, None),
    "successful_dribbles_per90": (0, None),
}

RELATIONSHIP_RULES = {
    "shots_on_target_gt_shots": (
        "shots_on_target",
        "shots",
    ),
    "successful_dribbles_gt_attempts": (
        "successful_dribbles",
        "dribble_attempts",
    ),
    "lineups_gt_appearances": (
        "lineups",
        "appearances",
    ),
}

RATE_EVIDENCE_RULES = {
    "shot_accuracy": {
        "attempts": "shots",
        "successes": "shots_on_target",
        "scored_groups": {"FW"},
        "prior_attempts": 12.0,
    },
    "dribble_success_rate": {
        "attempts": "dribble_attempts",
        "successes": "successful_dribbles",
        "scored_groups": {"FB", "W"},
        "prior_attempts": 12.0,
    },
}

ROBUST_METRICS = [
    "rating",
    "goals_per90",
    "assists_per90",
    "shots_per90",
    "shots_on_target_per90",
    "key_passes_per90",
    "tackles_per90",
    "interceptions_per90",
    "successful_dribbles_per90",
]


def _records(frame: pd.DataFrame, limit: int = 12) -> list[dict]:
    columns = [
        column
        for column in (
            "player_id",
            "name",
            "team",
            "position_group",
            "minutes",
        )
        if column in frame.columns
    ]
    extra = [column for column in frame.columns if column not in columns]
    selected = frame[columns + extra].head(limit).copy()
    selected = selected.replace({np.nan: None})
    return selected.to_dict(orient="records")


def _load_data(
    player_file: Path,
    tactical_file: Path,
) -> pd.DataFrame:
    data = pd.read_csv(player_file)

    if tactical_file.exists():
        tactical = pd.read_csv(
            tactical_file,
            usecols=["player_id", "position_group"],
        ).drop_duplicates("player_id")
        data = data.drop(
            columns=["position_group"],
            errors="ignore",
        ).merge(tactical, on="player_id", how="left")
    elif "position_group" not in data.columns:
        data["position_group"] = data.get(
            "detailed_position",
            "Unknown",
        )

    return data


def _hard_violations(data: pd.DataFrame) -> dict:
    findings = {}

    for metric, (minimum, maximum) in HARD_BOUNDS.items():
        if metric not in data.columns:
            continue
        values = pd.to_numeric(data[metric], errors="coerce")
        invalid = pd.Series(False, index=data.index)
        if minimum is not None:
            invalid |= values.notna() & (values < minimum)
        if maximum is not None:
            invalid |= values.notna() & (values > maximum)
        rows = data.loc[invalid].copy()
        rows[metric] = values.loc[invalid]
        findings[metric] = {
            "count": int(invalid.sum()),
            "examples": _records(rows[[
                column
                for column in (
                    "player_id",
                    "name",
                    "team",
                    "position_group",
                    "minutes",
                    metric,
                )
                if column in rows.columns
            ]]),
        }

    return findings


def _missing_values(data: pd.DataFrame) -> dict:
    findings = {}

    for metric in HARD_BOUNDS:
        if metric not in data.columns:
            continue
        values = pd.to_numeric(data[metric], errors="coerce")
        missing = values.isna()
        if not missing.any():
            continue
        rows = data.loc[missing].copy()
        findings[metric] = {
            "count": int(missing.sum()),
            "examples": _records(rows[[
                column
                for column in (
                    "player_id",
                    "name",
                    "team",
                    "position_group",
                    "minutes",
                    metric,
                )
                if column in rows.columns
            ]]),
        }

    return findings


def _relationship_violations(data: pd.DataFrame) -> dict:
    findings = {}

    for name, (left, right) in RELATIONSHIP_RULES.items():
        if left not in data.columns or right not in data.columns:
            continue
        left_values = pd.to_numeric(data[left], errors="coerce")
        right_values = pd.to_numeric(data[right], errors="coerce")
        invalid = left_values > right_values
        rows = data.loc[invalid].copy()
        findings[name] = {
            "count": int(invalid.sum()),
            "examples": _records(rows[[
                column
                for column in (
                    "player_id",
                    "name",
                    "team",
                    "position_group",
                    "minutes",
                    left,
                    right,
                )
                if column in rows.columns
            ]]),
        }

    return findings


def _rate_evidence_risks(data: pd.DataFrame) -> dict:
    findings = {}

    for metric, rule in RATE_EVIDENCE_RULES.items():
        required = {
            metric,
            rule["attempts"],
            rule["successes"],
            "position_group",
        }
        if not required.issubset(data.columns):
            continue

        attempts = pd.to_numeric(
            data[rule["attempts"]],
            errors="coerce",
        ).fillna(0).clip(lower=0)
        successes = pd.to_numeric(
            data[rule["successes"]],
            errors="coerce",
        ).fillna(0).clip(lower=0)
        successes = successes.where(successes <= attempts, attempts)

        group_attempts = attempts.groupby(
            data["position_group"]
        ).transform("sum")
        group_successes = successes.groupby(
            data["position_group"]
        ).transform("sum")
        global_rate = (
            float(successes.sum()) / float(attempts.sum())
            if float(attempts.sum()) > 0
            else 0.5
        )
        group_rate = (
            group_successes
            .div(group_attempts.where(group_attempts > 0))
            .fillna(global_rate)
            .clip(0, 1)
        )
        prior_attempts = float(rule["prior_attempts"])
        adjusted = (
            successes + group_rate * prior_attempts
        ) / (attempts + prior_attempts) * 100
        raw = pd.to_numeric(data[metric], errors="coerce")

        risk = (
            data["position_group"].isin(rule["scored_groups"])
            & (attempts < prior_attempts)
            & ((raw - adjusted).abs() >= 10)
        )
        rows = data.loc[risk, [
            column
            for column in (
                "player_id",
                "name",
                "team",
                "position_group",
                "minutes",
                metric,
                rule["attempts"],
                rule["successes"],
            )
            if column in data.columns
        ]].copy()
        rows["sample_adjusted_value"] = adjusted.loc[risk].round(2)
        rows["raw_adjustment"] = (
            raw.loc[risk] - adjusted.loc[risk]
        ).round(2)
        rows = rows.sort_values(
            "raw_adjustment",
            key=lambda values: values.abs(),
            ascending=False,
        )
        findings[metric] = {
            "count": int(risk.sum()),
            "examples": _records(rows),
        }

    return findings


def _robust_review_candidates(data: pd.DataFrame) -> list[dict]:
    eligible = data[
        pd.to_numeric(data.get("minutes"), errors="coerce") >= 450
    ].copy()
    candidates = []

    for group, group_data in eligible.groupby("position_group"):
        if len(group_data) < 20:
            continue
        for metric in ROBUST_METRICS:
            if metric not in group_data.columns:
                continue
            values = pd.to_numeric(group_data[metric], errors="coerce")
            median = float(values.median())
            mad = float((values - median).abs().median())
            if not np.isfinite(mad) or mad <= 0:
                continue
            robust_z = 0.6745 * (values - median) / mad
            flagged = robust_z.abs() > 5
            for index in group_data.index[flagged]:
                candidates.append({
                    "player_id": int(data.at[index, "player_id"]),
                    "name": str(data.at[index, "name"]),
                    "team": str(data.at[index, "team"]),
                    "position_group": str(group),
                    "minutes": float(data.at[index, "minutes"]),
                    "metric": metric,
                    "value": float(values.at[index]),
                    "group_median": round(median, 3),
                    "robust_z": round(float(robust_z.at[index]), 2),
                })

    return sorted(
        candidates,
        key=lambda item: abs(item["robust_z"]),
        reverse=True,
    )[:40]


def audit_player_data(
    player_file: Path = DEFAULT_PLAYER_FILE,
    tactical_file: Path = DEFAULT_TACTICAL_FILE,
) -> dict:
    data = _load_data(player_file, tactical_file)
    hard = _hard_violations(data)
    missing = _missing_values(data)
    relationships = _relationship_violations(data)
    rate_risks = _rate_evidence_risks(data)
    review = _robust_review_candidates(data)

    return {
        "dataset": str(player_file),
        "rows": int(len(data)),
        "hard_error_count": sum(
            item["count"] for item in hard.values()
        ),
        "missing_value_count": sum(
            item["count"] for item in missing.values()
        ),
        "relationship_error_count": sum(
            item["count"] for item in relationships.values()
        ),
        "model_relevant_low_sample_rate_count": sum(
            item["count"] for item in rate_risks.values()
        ),
        "hard_bounds": hard,
        "missing_values": missing,
        "relationship_rules": relationships,
        "low_sample_rate_risks": rate_risks,
        "robust_review_candidates": review,
        "note": (
            "Robust outliers are review candidates, not automatic errors. "
            "Elite football performance can be genuinely extreme."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--players",
        type=Path,
        default=DEFAULT_PLAYER_FILE,
    )
    parser.add_argument(
        "--tactical",
        type=Path,
        default=DEFAULT_TACTICAL_FILE,
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = audit_player_data(args.players, args.tactical)
    payload = json.dumps(report, indent=2, ensure_ascii=False)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()
