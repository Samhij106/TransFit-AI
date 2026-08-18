import argparse
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path
import re
import unicodedata
from urllib.request import Request, urlopen

import pandas as pd


PLAYERS_URL = (
    "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/"
    "data/players.csv.gz"
)
VALUATIONS_URL = (
    "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/"
    "data/player_valuations.csv.gz"
)
APPEARANCES_URL = (
    "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/"
    "data/appearances.csv.gz"
)
GAMES_URL = (
    "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/"
    "data/games.csv.gz"
)
LINEUPS_URL = (
    "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/"
    "data/game_lineups.csv.gz"
)
REEP_PEOPLE_URL = (
    "https://raw.githubusercontent.com/withqwerty/reep/"
    "main/data/people.csv"
)

PROFILES_PATH = Path(
    "data/processed/player_profiles_2025.csv"
)
EXTERNAL_DIR = Path(
    "data/external/transfermarkt"
)
PLAYERS_PATH = EXTERNAL_DIR / "players.csv.gz"
VALUATIONS_PATH = (
    EXTERNAL_DIR / "player_valuations.csv.gz"
)
APPEARANCES_PATH = (
    EXTERNAL_DIR / "appearances.csv.gz"
)
GAMES_PATH = EXTERNAL_DIR / "games.csv.gz"
LINEUPS_PATH = (
    EXTERNAL_DIR / "game_lineups.csv.gz"
)
REEP_PATH = Path(
    "data/external/reep/people.csv"
)
OUTPUT_PATH = Path(
    "data/processed/player_market_values_2025.csv"
)
UNMATCHED_PATH = Path(
    "data/processed/player_market_values_unmatched_2025.csv"
)

LEAGUE_CODES = {
    "Premier League": "GB1",
    "La Liga": "ES1",
    "Serie A": "IT1",
    "Bundesliga": "L1",
    "Ligue 1": "FR1",
}

SOURCE_POSITION_GROUPS = {
    "attacker": "Attack",
    "midfielder": "Midfield",
    "defender": "Defender",
    "goalkeeper": "Goalkeeper",
}

CHARACTER_REPLACEMENTS = str.maketrans({
    "ß": "ss",
    "ø": "o",
    "ł": "l",
    "đ": "d",
    "ð": "d",
    "þ": "th",
})

CLUB_ALIASES = {
    "bayern munchen": "bayern munich",
    "inter": "inter milan",
    "paris saint germain": "paris saint germain",
    "1 fc koln": "fc koln",
    "borussia monchengladbach": "borussia gladbach",
    "athletic club": "athletic bilbao",
    "real betis": "real betis balompie",
}


def normalize_text(value):
    if pd.isna(value):
        return ""

    value = str(value).strip().lower()
    value = value.translate(
        CHARACTER_REPLACEMENTS
    )
    value = unicodedata.normalize(
        "NFKD",
        value,
    )
    value = "".join(
        character
        for character in value
        if not unicodedata.combining(
            character
        )
    )
    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )
    return " ".join(
        value.split()
    )


def normalize_club(value):
    normalized = normalize_text(value)
    return CLUB_ALIASES.get(
        normalized,
        normalized,
    )


def token_set(value):
    return set(
        normalize_text(value).split()
    )


def position_groups_compatible(
    source_group,
    transfermarkt_group,
):
    if (
        not source_group
        or pd.isna(transfermarkt_group)
    ):
        return True

    source_is_goalkeeper = (
        source_group == "Goalkeeper"
    )
    target_is_goalkeeper = (
        transfermarkt_group == "Goalkeeper"
    )

    return (
        source_is_goalkeeper
        == target_is_goalkeeper
    )


def safe_ratio(left, right):
    if not left or not right:
        return 0.0

    return SequenceMatcher(
        None,
        left,
        right,
    ).ratio()


def calculate_age(
    date_of_birth,
    reference_date=date(2026, 6, 30),
):
    if pd.isna(date_of_birth):
        return None

    born = pd.Timestamp(
        date_of_birth
    ).date()

    return (
        reference_date.year
        - born.year
        - (
            (
                reference_date.month,
                reference_date.day,
            )
            < (born.month, born.day)
        )
    )


def download_file(url, target):
    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    temporary = target.with_suffix(
        target.suffix + ".tmp"
    )

    request = Request(
        url,
        headers={
            "User-Agent": (
                "TransFit-AI/1.0 market-value refresh"
            )
        },
    )

    with urlopen(
        request,
        timeout=300,
    ) as response, temporary.open(
        "wb"
    ) as output:
        while True:
            chunk = response.read(
                1024 * 1024
            )
            if not chunk:
                break
            output.write(chunk)

    temporary.replace(target)


def prepare_transfermarkt_players(players):
    players = players.copy()
    players = players[
        players["market_value_in_eur"]
        .notna()
    ].copy()

    players["normalized_name"] = (
        players["name"].apply(
            normalize_text
        )
    )
    players["normalized_first_name"] = (
        players["first_name"].apply(
            normalize_text
        )
    )
    players["surname_tokens"] = (
        players.apply(
            lambda row: token_set(
                row["last_name"]
            )
            or {
                row["normalized_name"]
                .split()[-1]
            },
            axis=1,
        )
    )
    players["name_tokens"] = (
        players["name"].apply(
            token_set
        )
    )
    players["normalized_club"] = (
        players["current_club_name"].apply(
            normalize_club
        )
    )
    players["calculated_age"] = (
        players["date_of_birth"].apply(
            calculate_age
        )
    )

    return players


def build_surname_index(players):
    index = {}

    for row_index, row in (
        players.iterrows()
    ):
        for surname in row[
            "surname_tokens"
        ]:
            index.setdefault(
                surname,
                [],
            ).append(row_index)

    return index


def load_provider_id_map():
    people = pd.read_csv(
        REEP_PATH,
        usecols=[
            "key_api_football",
            "key_transfermarkt",
        ],
        dtype=str,
        low_memory=False,
    ).dropna()

    mapping = {}

    for _, row in people.iterrows():
        try:
            api_football_id = int(
                float(row["key_api_football"])
            )
            transfermarkt_id = int(
                float(row["key_transfermarkt"])
            )
        except (TypeError, ValueError):
            continue

        mapping.setdefault(
            api_football_id,
            transfermarkt_id,
        )

    return mapping


def internal_identity(row):
    full_name = normalize_text(
        f"{row['firstname']} "
        f"{row['lastname']}"
    )
    display_name = normalize_text(
        row["name"]
    )
    first_name = normalize_text(
        row["firstname"]
    )
    last_name = normalize_text(
        row["lastname"]
    )

    surname_tokens = token_set(
        row["lastname"]
    )

    if display_name:
        surname_tokens.add(
            display_name.split()[-1]
        )

    return {
        "full_name": full_name,
        "display_name": display_name,
        "first_name": first_name,
        "last_name": last_name,
        "name_tokens": set(
            full_name.split()
        ),
        "surname_tokens": surname_tokens,
        "club": normalize_club(
            row["team"]
        ),
        "age": float(row["age"]),
        "league_code": LEAGUE_CODES.get(
            row["league"]
        ),
        "position_group": SOURCE_POSITION_GROUPS.get(
            normalize_text(row.get("position"))
        ),
    }


def score_candidate(identity, candidate):
    candidate_name = candidate[
        "normalized_name"
    ]
    candidate_tokens = candidate[
        "name_tokens"
    ]

    name_similarity = max(
        safe_ratio(
            identity["full_name"],
            candidate_name,
        ),
        safe_ratio(
            identity["display_name"],
            candidate_name,
        ),
    )

    if candidate_tokens:
        token_coverage = (
            len(
                identity["name_tokens"]
                & candidate_tokens
            )
            / len(candidate_tokens)
        )
    else:
        token_coverage = 0.0

    surname_match = float(
        bool(
            identity["surname_tokens"]
            & candidate["surname_tokens"]
        )
    )

    internal_first = (
        identity["first_name"].split()[0]
        if identity["first_name"]
        else ""
    )
    candidate_first = (
        candidate[
            "normalized_first_name"
        ].split()[0]
        if candidate[
            "normalized_first_name"
        ]
        else ""
    )

    first_name_match = float(
        internal_first == candidate_first
        and bool(internal_first)
    )

    candidate_age = candidate[
        "calculated_age"
    ]
    if candidate_age is None or pd.isna(
        candidate_age
    ):
        age_score = 0.5
        age_difference = None
    else:
        age_difference = abs(
            identity["age"]
            - float(candidate_age)
        )
        if age_difference <= 1:
            age_score = 1.0
        elif age_difference <= 2:
            age_score = 0.6
        else:
            age_score = 0.0

    club_similarity = safe_ratio(
        identity["club"],
        candidate["normalized_club"],
    )
    league_match = float(
        identity["league_code"]
        == candidate[
            "current_club_domestic_competition_id"
        ]
    )

    score = (
        name_similarity * 0.32
        + token_coverage * 0.20
        + surname_match * 0.14
        + first_name_match * 0.08
        + age_score * 0.14
        + club_similarity * 0.09
        + league_match * 0.03
    )

    return {
        "score": round(score, 4),
        "name_similarity": name_similarity,
        "token_coverage": token_coverage,
        "surname_match": surname_match,
        "first_name_match": first_name_match,
        "age_difference": age_difference,
        "club_similarity": club_similarity,
        "league_match": league_match,
    }


def find_best_match(
    row,
    players,
    surname_index,
    players_by_id,
    provider_id_map,
):
    api_football_id = int(
        row["player_id"]
    )
    transfermarkt_id = provider_id_map.get(
        api_football_id
    )

    identity = internal_identity(row)

    if transfermarkt_id in players_by_id:
        mapped_candidate = players_by_id[
            transfermarkt_id
        ]
        mapped_position = mapped_candidate.get(
            "position"
        )
        position_is_compatible = (
            position_groups_compatible(
                identity["position_group"],
                mapped_position,
            )
        )

        if position_is_compatible:
            return {
                "accepted": True,
                "confidence": "high",
                "score": 1.0,
                "margin": 1.0,
                "candidate": mapped_candidate,
                "details": {},
                "method": "provider_id_crosswalk",
            }

    candidate_indexes = set()

    for surname in identity[
        "surname_tokens"
    ]:
        candidate_indexes.update(
            surname_index.get(
                surname,
                [],
            )
        )

    if not candidate_indexes:
        return None

    scored = []

    for candidate_index in candidate_indexes:
        candidate = players.loc[
            candidate_index
        ]

        if not position_groups_compatible(
            identity["position_group"],
            candidate.get("position"),
        ):
            continue

        details = score_candidate(
            identity,
            candidate,
        )
        scored.append(
            (
                details["score"],
                candidate,
                details,
            )
        )

    if not scored:
        return None

    scored.sort(
        key=lambda result: result[0],
        reverse=True,
    )

    best_score, best, details = scored[0]
    second_score = (
        scored[1][0]
        if len(scored) > 1
        else 0.0
    )
    margin = best_score - second_score

    exact_name = (
        best["normalized_name"]
        == identity["full_name"]
    )
    strong_identity = (
        details["token_coverage"] >= 0.8
        and details["surname_match"] == 1
        and details["first_name_match"] == 1
        and (
            details["age_difference"] is None
            or details["age_difference"] <= 1
        )
    )

    accepted = (
        (
            best_score >= 0.82
            and margin >= 0.025
        )
        or (
            exact_name
            and best_score >= 0.78
        )
        or (
            strong_identity
            and best_score >= 0.80
            and margin >= 0.015
        )
    )

    if best_score >= 0.90 and margin >= 0.05:
        confidence = "high"
    elif accepted:
        confidence = "medium"
    else:
        confidence = "unmatched"

    return {
        "accepted": accepted,
        "confidence": confidence,
        "score": best_score,
        "margin": round(margin, 4),
        "candidate": best,
        "details": details,
        "method": "name_club_age",
    }


def latest_valuation_dates(valuations):
    valuations = valuations.copy()
    valuations["date"] = pd.to_datetime(
        valuations["date"],
        errors="coerce",
    )
    valuations = valuations.sort_values(
        "date"
    )
    latest = valuations.groupby(
        "player_id",
        as_index=False,
    ).tail(1)

    return {
        int(row["player_id"]): (
            None
            if pd.isna(row["date"])
            else row["date"].date().isoformat()
        )
        for _, row in latest.iterrows()
    }


def build_market_values():
    profiles = pd.read_csv(
        PROFILES_PATH
    )
    profiles = profiles.drop_duplicates(
        subset=["player_id"],
        keep="first",
    )

    players = prepare_transfermarkt_players(
        pd.read_csv(PLAYERS_PATH)
    )
    valuation_dates = latest_valuation_dates(
        pd.read_csv(VALUATIONS_PATH)
    )
    surname_index = build_surname_index(
        players
    )
    players_by_id = {
        int(row["player_id"]): row
        for _, row in players.iterrows()
    }
    provider_id_map = load_provider_id_map()

    matched_rows = []
    unmatched_rows = []

    for _, profile in profiles.iterrows():
        match = find_best_match(
            profile,
            players,
            surname_index,
            players_by_id,
            provider_id_map,
        )

        base = {
            "api_football_player_id": int(
                profile["player_id"]
            ),
            "player_name": profile["name"],
            "player_full_name": (
                f"{profile['firstname']} "
                f"{profile['lastname']}"
            ).strip(),
            "current_team": profile["team"],
            "league": profile["league"],
        }

        if match is None:
            unmatched_rows.append({
                **base,
                "reason": "no_surname_candidate",
                "best_transfermarkt_name": None,
                "best_match_score": None,
                "best_match_margin": None,
            })
            continue

        candidate = match["candidate"]

        if not match["accepted"]:
            unmatched_rows.append({
                **base,
                "reason": "low_or_ambiguous_score",
                "best_transfermarkt_name": (
                    candidate["name"]
                ),
                "best_match_score": match["score"],
                "best_match_margin": match["margin"],
            })
            continue

        transfermarkt_id = int(
            candidate["player_id"]
        )
        value_eur = int(
            candidate["market_value_in_eur"]
        )

        matched_rows.append({
            **base,
            "transfermarkt_player_id": transfermarkt_id,
            "transfermarkt_name": candidate["name"],
            "transfermarkt_club": candidate[
                "current_club_name"
            ],
            "market_value_eur": value_eur,
            "market_value_m_eur": round(
                value_eur / 1_000_000,
                2,
            ),
            "valuation_date": valuation_dates.get(
                transfermarkt_id
            ),
            "transfermarkt_url": candidate["url"],
            "match_confidence": match["confidence"],
            "match_score": match["score"],
            "match_margin": match["margin"],
            "match_method": match["method"],
            "source": "transfermarkt_dataset",
        })

    matched = pd.DataFrame(matched_rows)
    unmatched = pd.DataFrame(unmatched_rows)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    matched.sort_values(
        ["league", "current_team", "player_name"]
    ).to_csv(
        OUTPUT_PATH,
        index=False,
    )
    unmatched.sort_values(
        ["league", "current_team", "player_name"]
    ).to_csv(
        UNMATCHED_PATH,
        index=False,
    )

    total = len(profiles)
    match_rate = (
        len(matched) / total * 100
        if total
        else 0
    )

    print(
        f"Matched {len(matched):,}/{total:,} "
        f"players ({match_rate:.1f}%)."
    )
    print(
        f"Unmatched: {len(unmatched):,}."
    )
    print(
        f"Market values: {OUTPUT_PATH}"
    )
    print(
        f"Review report: {UNMATCHED_PATH}"
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Refresh Transfermarkt-based player market values."
        )
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help=(
            "Download the latest weekly source files before matching."
        ),
    )
    args = parser.parse_args()

    if args.download:
        print("Downloading Transfermarkt player snapshot...")
        download_file(
            PLAYERS_URL,
            PLAYERS_PATH,
        )
        print("Downloading valuation history...")
        download_file(
            VALUATIONS_URL,
            VALUATIONS_PATH,
        )
        print("Downloading all-competition appearances...")
        download_file(
            APPEARANCES_URL,
            APPEARANCES_PATH,
        )
        print("Downloading match records...")
        download_file(
            GAMES_URL,
            GAMES_PATH,
        )
        print("Downloading verified lineups and positions...")
        download_file(
            LINEUPS_URL,
            LINEUPS_PATH,
        )
        print("Downloading provider ID crosswalk...")
        download_file(
            REEP_PEOPLE_URL,
            REEP_PATH,
        )

    missing = [
        str(path)
        for path in (
            PLAYERS_PATH,
            VALUATIONS_PATH,
            APPEARANCES_PATH,
            GAMES_PATH,
            LINEUPS_PATH,
            REEP_PATH,
        )
        if not path.exists()
    ]
    if missing:
        raise SystemExit(
            "Missing source files: "
            + ", ".join(missing)
            + ". Run with --download."
        )

    build_market_values()


if __name__ == "__main__":
    main()
