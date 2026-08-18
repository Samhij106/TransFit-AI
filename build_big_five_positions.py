from pathlib import Path

import numpy as np
import pandas as pd


RAW_FILE = Path("data/raw/big_five_players_2025.csv")
KNOWN_POSITIONS_FILE = Path(
    "data/processed/player_positions_2025.csv"
)
OUTPUT_FILE = Path(
    "data/processed/player_positions_big_five_2025.csv"
)


COUNTING_STATS = [
    "goals",
    "assists",
    "shots",
    "shots_on_target",
    "passes",
    "key_passes",
    "tackles",
    "blocks",
    "interceptions",
    "dribble_attempts",
    "successful_dribbles",
    "duels_total",
    "duels_won",
]


def percentile(series):
    return series.rank(
        pct=True,
        method="average",
    ).fillna(0.5) * 100


def average(row, columns):
    return float(
        np.mean([
            row[column]
            for column in columns
        ])
    )


def confidence_from_margin(
    first_score,
    second_score,
    maximum=72,
):
    margin = abs(
        float(first_score)
        - float(second_score)
    )

    return round(
        min(
            maximum,
            55 + margin * 0.25,
        ),
        1,
    )


def infer_position(row):
    broad = str(
        row.get("position", "")
    ).strip()

    if broad == "Goalkeeper":
        return "GK", None, 100.0

    if broad == "Defender":
        wide_score = average(
            row,
            [
                "assists_per90_pct",
                "key_passes_per90_pct",
                "dribble_attempts_per90_pct",
                "successful_dribbles_per90_pct",
            ],
        )

        central_score = average(
            row,
            [
                "blocks_per90_pct",
                "interceptions_per90_pct",
                "duels_won_per90_pct",
                "passes_per90_pct",
            ],
        )

        if (
            wide_score >= 62
            and wide_score > central_score
        ):
            return (
                "FB",
                None,
                confidence_from_margin(
                    wide_score,
                    central_score,
                    maximum=68,
                ),
            )

        return (
            "CB",
            None,
            confidence_from_margin(
                central_score,
                wide_score,
            ),
        )

    if broad == "Midfielder":
        defensive_score = average(
            row,
            [
                "tackles_per90_pct",
                "interceptions_per90_pct",
                "blocks_per90_pct",
                "duels_won_per90_pct",
            ],
        )

        creative_score = average(
            row,
            [
                "assists_per90_pct",
                "key_passes_per90_pct",
                "shots_per90_pct",
                "shots_on_target_per90_pct",
            ],
        )

        wide_score = average(
            row,
            [
                "dribble_attempts_per90_pct",
                "successful_dribbles_per90_pct",
                "assists_per90_pct",
                "shots_per90_pct",
            ],
        )

        if (
            wide_score >= 72
            and row[
                "dribble_attempts_per90_pct"
            ] >= 70
            and (
                wide_score
                > max(
                    defensive_score,
                    creative_score,
                )
                or row["passes_per90_pct"] < 70
            )
        ):
            second = max(
                defensive_score,
                creative_score,
            )

            return (
                "W",
                "CAM",
                confidence_from_margin(
                    wide_score,
                    second,
                    maximum=68,
                ),
            )

        if (
            creative_score >= 65
            and creative_score
            >= defensive_score + 8
        ):
            return (
                "CAM",
                "W"
                if (
                    wide_score >= 75
                    and row[
                        "dribble_attempts_per90_pct"
                    ] >= 70
                )
                else "CM",
                confidence_from_margin(
                    creative_score,
                    defensive_score,
                ),
            )

        if (
            defensive_score >= 62
            and defensive_score
            >= creative_score + 8
        ):
            return (
                "CDM",
                "CM",
                confidence_from_margin(
                    defensive_score,
                    creative_score,
                ),
            )

        return "CM", None, 58.0

    if broad in {
        "Attacker",
        "Forward",
    }:
        central_score = average(
            row,
            [
                "goals_per90_pct",
                "shots_per90_pct",
                "shots_on_target_per90_pct",
                "duels_won_per90_pct",
            ],
        )

        wide_score = average(
            row,
            [
                "assists_per90_pct",
                "key_passes_per90_pct",
                "dribble_attempts_per90_pct",
                "successful_dribbles_per90_pct",
            ],
        )

        if (
            wide_score >= 62
            and row[
                "dribble_attempts_per90_pct"
            ] >= 70
            and row[
                "key_passes_per90_pct"
            ] >= 60
        ):
            return (
                "W",
                "ST"
                if central_score
                >= wide_score - 8
                else None,
                confidence_from_margin(
                    wide_score,
                    central_score,
                    maximum=68,
                ),
            )

        return (
            "ST",
            "W"
            if wide_score >= central_score - 6
            else None,
            confidence_from_margin(
                central_score,
                wide_score,
            ),
        )

    return "Unknown", None, 0.0


def prepare_inference_data(raw):
    data = raw.copy()

    numeric_columns = [
        "minutes",
        *COUNTING_STATS,
    ]

    for column in numeric_columns:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
        ).fillna(0)

    base_indexes = (
        data.groupby("player_id")["minutes"]
        .idxmax()
    )

    base = (
        data.loc[
            base_indexes,
            [
                "player_id",
                "name",
                "position",
            ],
        ]
        .set_index("player_id")
    )

    totals = data.groupby(
        "player_id"
    )[
        [
            "minutes",
            *COUNTING_STATS,
        ]
    ].sum()

    players = base.join(
        totals,
        how="inner",
    ).reset_index()

    safe_minutes = players[
        "minutes"
    ].replace(0, np.nan)

    for column in COUNTING_STATS:
        metric = f"{column}_per90"

        players[metric] = (
            players[column]
            / safe_minutes
            * 90
        ).fillna(0)

        players[f"{metric}_pct"] = (
            players.groupby("position")[metric]
            .transform(percentile)
        )

    return players


def build_position_rows(raw, known_positions):
    inference_data = prepare_inference_data(
        raw
    )

    known_by_id = {
        int(row["player_id"]): row
        for _, row in known_positions.iterrows()
    }

    rows = []

    for _, player in inference_data.iterrows():
        player_id = int(
            player["player_id"]
        )

        known = known_by_id.get(
            player_id
        )

        if known is not None:
            row = {
                column: known.get(column)
                for column in [
                    "player_id",
                    "name",
                    "primary_position",
                    "primary_starts",
                    "secondary_position",
                    "secondary_starts",
                    "total_starts",
                    "position_confidence",
                    "unknown_starts",
                    "position_history",
                ]
            }

            row["name"] = player["name"]
            row["position_source"] = (
                "lineup_history"
            )
            row["broad_position"] = (
                player["position"]
            )

            rows.append(row)
            continue

        (
            primary,
            secondary,
            confidence,
        ) = infer_position(player)

        rows.append({
            "player_id": player_id,
            "name": player["name"],
            "primary_position": primary,
            "primary_starts": 0,
            "secondary_position": secondary,
            "secondary_starts": 0,
            "total_starts": 0,
            "position_confidence": confidence,
            "unknown_starts": 0,
            "position_history": "",
            "position_source": (
                "statistical_fallback"
            ),
            "broad_position": (
                player["position"]
            ),
        })

    return pd.DataFrame(rows)


def main():
    raw = pd.read_csv(RAW_FILE)
    known_positions = pd.read_csv(
        KNOWN_POSITIONS_FILE
    )

    positions = build_position_rows(
        raw,
        known_positions,
    )

    positions = positions.sort_values(
        [
            "primary_position",
            "position_confidence",
            "name",
        ],
        ascending=[
            True,
            False,
            True,
        ],
    ).reset_index(drop=True)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    positions.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("BIG FIVE POSITION PROFILES")
    print()
    print(
        f"Players: {len(positions)}"
    )
    print(
        positions[
            "position_source"
        ].value_counts().to_string()
    )
    print()
    print(
        positions[
            "primary_position"
        ].value_counts().to_string()
    )
    print()
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
