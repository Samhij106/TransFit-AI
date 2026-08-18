import os
import time
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

from league_config import LEAGUES


FIXTURES_URL = "https://v3.football.api-sports.io/fixtures"
FORMATION_OUTPUT = Path(
    "data/processed/team_formation_profiles_2025.csv"
)
TACTICAL_OUTPUT = Path(
    "data/processed/team_tactical_profiles_2025.csv"
)
MIN_MATCHES_ANALYZED = 10
BATCH_SIZE = 20


def chunk_list(items, size):
    for index in range(0, len(items), size):
        yield items[index:index + size]


def numeric_value(value):
    if value is None:
        return None

    if isinstance(value, str):
        value = value.replace("%", "").strip()

        if not value:
            return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def percentile_score(value, series):
    clean = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if clean.empty:
        return 50.0

    return round(
        (clean <= value).mean() * 100,
        1,
    )


def get_json(session, headers, params):
    response = session.get(
        FIXTURES_URL,
        headers=headers,
        params=params,
        timeout=45,
    )
    response.raise_for_status()

    data = response.json()
    errors = data.get("errors")

    if errors:
        raise RuntimeError(
            f"API-Football error: {errors}"
        )

    return data.get("response", [])


def extract_match_statistics(team_block):
    stats = {}

    for statistic in team_block.get(
        "statistics",
        [],
    ):
        stats[statistic.get("type")] = (
            numeric_value(
                statistic.get("value")
            )
        )

    return {
        "possession": stats.get(
            "Ball Possession"
        ),
        "total_shots": stats.get(
            "Total Shots"
        ),
        "shots_on_target": stats.get(
            "Shots on Goal"
        ),
        "shots_inside_box": stats.get(
            "Shots insidebox"
        ),
        "corners": stats.get(
            "Corner Kicks"
        ),
        "total_passes": stats.get(
            "Total passes"
        ),
        "accurate_passes": stats.get(
            "Passes accurate"
        ),
        "pass_accuracy": stats.get(
            "Passes %"
        ),
    }


def collect_fixture_data(headers):
    team_formations = defaultdict(Counter)
    team_matches = defaultdict(list)
    team_metadata = {}

    with requests.Session() as session:
        for league in LEAGUES:
            print()
            print("=" * 70)
            print(
                f"{league['name']} "
                f"{league['season']}"
            )
            print("=" * 70)

            fixtures = get_json(
                session,
                headers,
                {
                    "league": league["id"],
                    "season": league["season"],
                    "status": "FT-AET-PEN",
                },
            )

            fixture_ids = [
                fixture["fixture"]["id"]
                for fixture in fixtures
            ]

            batches = list(
                chunk_list(
                    fixture_ids,
                    BATCH_SIZE,
                )
            )

            print(
                f"Completed fixtures: "
                f"{len(fixture_ids)}"
            )
            print(
                f"Fixture batches: {len(batches)}"
            )

            for batch_index, fixture_group in enumerate(
                batches,
                start=1,
            ):
                ids = "-".join(
                    str(fixture_id)
                    for fixture_id in fixture_group
                )

                full_fixtures = get_json(
                    session,
                    headers,
                    {"ids": ids},
                )

                for fixture in full_fixtures:
                    for lineup in fixture.get(
                        "lineups",
                        [],
                    ):
                        team = lineup.get(
                            "team",
                            {},
                        )
                        team_id = team.get("id")
                        formation = lineup.get(
                            "formation"
                        )

                        if not team_id or not formation:
                            continue

                        team_formations[
                            int(team_id)
                        ][formation] += 1

                    for team_block in fixture.get(
                        "statistics",
                        [],
                    ):
                        team = team_block.get(
                            "team",
                            {},
                        )
                        team_id = team.get("id")
                        team_name = team.get("name")

                        if not team_id:
                            continue

                        team_id = int(team_id)

                        team_metadata[team_id] = {
                            "league_id": league["id"],
                            "league": league["name"],
                            "season": league["season"],
                            "team_id": team_id,
                            "team": team_name,
                        }

                        team_matches[team_id].append(
                            extract_match_statistics(
                                team_block
                            )
                        )

                print(
                    f"Batch {batch_index}/"
                    f"{len(batches)} processed"
                )
                time.sleep(0.25)

    return (
        team_formations,
        team_matches,
        team_metadata,
    )


def build_formation_profiles(
    team_formations,
    eligible_team_ids,
    team_metadata,
):
    rows = []

    for team_id in sorted(eligible_team_ids):
        formation_counter = team_formations.get(
            team_id,
            Counter(),
        )

        if not formation_counter:
            continue

        ranked = formation_counter.most_common()
        total_matches = sum(
            formation_counter.values()
        )
        primary, primary_matches = ranked[0]

        if len(ranked) >= 2:
            secondary, secondary_matches = (
                ranked[1]
            )
        else:
            secondary = None
            secondary_matches = 0

        history = " | ".join(
            f"{formation}:{count}"
            for formation, count in ranked
        )

        rows.append({
            **team_metadata[team_id],
            "matches_analyzed": total_matches,
            "primary_formation": primary,
            "primary_matches": primary_matches,
            "primary_percentage": round(
                primary_matches
                / total_matches
                * 100,
                1,
            ),
            "secondary_formation": secondary,
            "secondary_matches": (
                secondary_matches
            ),
            "secondary_percentage": round(
                secondary_matches
                / total_matches
                * 100,
                1,
            ),
            "formation_history": history,
        })

    return pd.DataFrame(rows)


def build_tactical_profiles(
    team_matches,
    eligible_team_ids,
    team_metadata,
):
    rows = []

    for team_id in sorted(eligible_team_ids):
        matches = team_matches[team_id]
        match_data = pd.DataFrame(matches)
        averages = match_data.mean(
            numeric_only=True
        )

        shots = averages.get(
            "total_shots",
            0,
        )
        target = averages.get(
            "shots_on_target",
            0,
        )
        passes = averages.get(
            "total_passes",
            0,
        )

        shots_per_100_passes = (
            shots / passes * 100
            if pd.notna(passes) and passes > 0
            else 0
        )
        shot_accuracy = (
            target / shots * 100
            if pd.notna(shots) and shots > 0
            else 0
        )

        rows.append({
            **team_metadata[team_id],
            "matches_analyzed": len(matches),
            "avg_possession": round(
                averages.get("possession", 0),
                2,
            ),
            "avg_total_shots": round(
                shots,
                2,
            ),
            "avg_shots_on_target": round(
                target,
                2,
            ),
            "avg_shots_inside_box": round(
                averages.get(
                    "shots_inside_box",
                    0,
                ),
                2,
            ),
            "avg_corners": round(
                averages.get("corners", 0),
                2,
            ),
            "avg_total_passes": round(
                passes,
                2,
            ),
            "avg_accurate_passes": round(
                averages.get(
                    "accurate_passes",
                    0,
                ),
                2,
            ),
            "avg_pass_accuracy": round(
                averages.get(
                    "pass_accuracy",
                    0,
                ),
                2,
            ),
            "shots_per_100_passes": round(
                shots_per_100_passes,
                2,
            ),
            "shot_accuracy": round(
                shot_accuracy,
                2,
            ),
        })

    profiles = pd.DataFrame(rows)

    profiles["possession_control"] = (
        profiles["avg_possession"]
        .apply(
            lambda value: percentile_score(
                value,
                profiles["avg_possession"],
            )
        )
    )

    pass_volume = profiles[
        "avg_total_passes"
    ].apply(
        lambda value: percentile_score(
            value,
            profiles["avg_total_passes"],
        )
    )
    pass_accuracy = profiles[
        "avg_pass_accuracy"
    ].apply(
        lambda value: percentile_score(
            value,
            profiles["avg_pass_accuracy"],
        )
    )
    profiles["passing_control"] = (
        pass_volume * 0.45
        + pass_accuracy * 0.55
    ).round(1)

    shots_score = profiles[
        "avg_total_shots"
    ].apply(
        lambda value: percentile_score(
            value,
            profiles["avg_total_shots"],
        )
    )
    target_score = profiles[
        "avg_shots_on_target"
    ].apply(
        lambda value: percentile_score(
            value,
            profiles["avg_shots_on_target"],
        )
    )
    inside_score = profiles[
        "avg_shots_inside_box"
    ].apply(
        lambda value: percentile_score(
            value,
            profiles["avg_shots_inside_box"],
        )
    )

    profiles["chance_creation"] = (
        shots_score * 0.35
        + target_score * 0.35
        + inside_score * 0.30
    ).round(1)

    corner_score = profiles[
        "avg_corners"
    ].apply(
        lambda value: percentile_score(
            value,
            profiles["avg_corners"],
        )
    )

    profiles["attacking_pressure"] = (
        shots_score * 0.45
        + corner_score * 0.25
        + profiles["possession_control"] * 0.30
    ).round(1)

    profiles["directness"] = profiles[
        "shots_per_100_passes"
    ].apply(
        lambda value: percentile_score(
            value,
            profiles["shots_per_100_passes"],
        )
    )
    profiles["shooting_efficiency"] = (
        profiles["shot_accuracy"]
        .apply(
            lambda value: percentile_score(
                value,
                profiles["shot_accuracy"],
            )
        )
    )

    return profiles


def main():
    load_dotenv()
    api_key = os.getenv("API_FOOTBALL_KEY")

    if not api_key:
        raise SystemExit(
            "API_FOOTBALL_KEY is missing."
        )

    (
        team_formations,
        team_matches,
        team_metadata,
    ) = collect_fixture_data({
        "x-apisports-key": api_key,
    })

    eligible_team_ids = {
        team_id
        for team_id, matches
        in team_matches.items()
        if len(matches) >= MIN_MATCHES_ANALYZED
    }

    formations = build_formation_profiles(
        team_formations,
        eligible_team_ids,
        team_metadata,
    )
    tactical = build_tactical_profiles(
        team_matches,
        eligible_team_ids,
        team_metadata,
    )

    common_ids = (
        set(formations["team_id"])
        & set(tactical["team_id"])
    )

    formations = formations[
        formations["team_id"].isin(common_ids)
    ].sort_values(
        ["league", "team"]
    )
    tactical = tactical[
        tactical["team_id"].isin(common_ids)
    ].sort_values(
        ["league", "team"]
    )

    FORMATION_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    formations.to_csv(
        FORMATION_OUTPUT,
        index=False,
    )
    tactical.to_csv(
        TACTICAL_OUTPUT,
        index=False,
    )

    print()
    print("=" * 70)
    print("BIG FIVE TEAM PROFILES COMPLETE")
    print("=" * 70)
    print(
        formations.groupby("league")["team_id"]
        .nunique()
        .to_string()
    )
    print()
    print(
        f"Formation profiles: {len(formations)}"
    )
    print(
        f"Tactical profiles: {len(tactical)}"
    )
    print(f"Output: {FORMATION_OUTPUT}")
    print(f"Output: {TACTICAL_OUTPUT}")


if __name__ == "__main__":
    main()
