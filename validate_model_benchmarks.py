import argparse
import json
import sys
from pathlib import Path

from transfit_service import get_candidate_rankings


DEFAULT_BENCHMARK_FILE = (
    Path(__file__).parent
    / "data"
    / "benchmarks"
    / "transfit_v7_benchmarks.json"
)


def load_benchmark_suite(path):
    with path.open(encoding="utf-8") as benchmark_file:
        return json.load(benchmark_file)


def candidate_index(candidates):
    return {
        int(candidate["player_id"]): {
            "rank": rank,
            "score": float(candidate["final_score"]),
            "name": candidate["name"],
        }
        for rank, candidate in enumerate(candidates, start=1)
    }


def validate_group(group, expected_model_version):
    result = get_candidate_rankings(
        group["team"],
        group["role"],
        limit=group.get("limit", 300),
        min_minutes=group.get("min_minutes", 450),
        min_role_fit=group.get("min_role_fit", 80),
    )
    candidates = candidate_index(result["candidates"])
    failures = []
    checks = []

    actual_model_version = result["scoring_model"]["version"]
    if actual_model_version != expected_model_version:
        failures.append(
            "model version changed: "
            f"expected {expected_model_version!r}, got {actual_model_version!r}"
        )

    for case in group.get("ordered_pairs", []):
        preferred_id = int(case["preferred_player_id"])
        comparison_id = int(case["comparison_player_id"])
        preferred = candidates.get(preferred_id)
        comparison = candidates.get(comparison_id)
        label = (
            f"{case['preferred_name']} above "
            f"{case['comparison_name']}"
        )

        if preferred is None or comparison is None:
            missing = []
            if preferred is None:
                missing.append(case["preferred_name"])
            if comparison is None:
                missing.append(case["comparison_name"])
            failures.append(
                f"{label}: missing from ranking: {', '.join(missing)}"
            )
            continue

        score_gap = round(
            preferred["score"] - comparison["score"],
            1,
        )
        minimum_gap = float(case.get("minimum_score_gap", 0))
        passed = (
            preferred["rank"] < comparison["rank"]
            and score_gap >= minimum_gap
        )
        detail = (
            f"{label}: ranks {preferred['rank']} vs {comparison['rank']}, "
            f"scores {preferred['score']:.1f} vs {comparison['score']:.1f}, "
            f"gap {score_gap:+.1f}"
        )
        checks.append((passed, detail))
        if not passed:
            failures.append(
                f"{detail}; required gap >= {minimum_gap:.1f}"
            )

    for exclusion in group.get("excluded_players", []):
        player_id = int(exclusion["player_id"])
        is_absent = player_id not in candidates
        detail = (
            f"{exclusion['name']} excluded from {group['role']} "
            f"({exclusion['reason']})"
        )
        checks.append((is_absent, detail))
        if not is_absent:
            failures.append(
                f"{detail}; appeared at rank {candidates[player_id]['rank']}"
            )

    return checks, failures, len(candidates)


def run_suite(path):
    suite = load_benchmark_suite(path)
    expected_model_version = suite["model_version"]
    total_checks = 0
    all_failures = []

    print(f"TransFit benchmark suite v{suite['suite_version']}")
    print(f"Model: {expected_model_version}")

    for group in suite["groups"]:
        print(
            f"\n[{group['id']}] "
            f"{group['team']} / {group['role']}"
        )
        checks, failures, candidate_count = validate_group(
            group,
            expected_model_version,
        )
        print(f"Candidates evaluated: {candidate_count}")

        for passed, detail in checks:
            total_checks += 1
            status = "PASS" if passed else "FAIL"
            print(f"  {status}: {detail}")

        all_failures.extend(
            f"{group['id']}: {failure}"
            for failure in failures
        )

    print(
        f"\nResult: {total_checks - len(all_failures)}/{total_checks} "
        "checks passed"
    )

    if all_failures:
        print("\nFailures:")
        for failure in all_failures:
            print(f"  - {failure}")
        return 1

    return 0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run football sanity checks against TransFit rankings."
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_BENCHMARK_FILE,
        help="Path to the benchmark JSON file.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    sys.exit(run_suite(arguments.file))
