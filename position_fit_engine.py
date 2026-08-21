import argparse
import pandas as pd


PLAYER_FILE = (
    "data/processed/"
    "player_positions_big_five_2025.csv"
)
FORMATION_FILE = "data/processed/team_formation_profiles_2025.csv"
REALISM_FILE = (
    "data/processed/"
    "player_realism_profiles_2025.csv"
)


# =========================================================
# FORMATION ROLES
# =========================================================

FORMATION_ROLES = {
    "4-3-3": [
        "GK",
        "LB", "CB", "CB", "RB",
        "CDM", "CM", "CM",
        "LW", "ST", "RW",
    ],

    "4-2-3-1": [
        "GK",
        "LB", "CB", "CB", "RB",
        "CDM", "CDM",
        "LW", "CAM", "RW",
        "ST",
    ],

    "4-4-2": [
        "GK",
        "LB", "CB", "CB", "RB",
        "LM", "CM", "CM", "RM",
        "ST", "ST",
    ],

    "4-1-4-1": [
        "GK",
        "LB", "CB", "CB", "RB",
        "CDM",
        "LM", "CM", "CM", "RM",
        "ST",
    ],

    "4-2-2-2": [
        "GK",
        "LB", "CB", "CB", "RB",
        "CDM", "CDM",
        "CAM", "CAM",
        "ST", "ST",
    ],

    "4-3-1-2": [
        "GK",
        "LB", "CB", "CB", "RB",
        "CDM", "CM", "CM",
        "CAM",
        "ST", "ST",
    ],

    "4-3-2-1": [
        "GK",
        "LB", "CB", "CB", "RB",
        "CDM", "CM", "CM",
        "CAM", "CAM",
        "ST",
    ],

    "4-1-3-2": [
        "GK",
        "LB", "CB", "CB", "RB",
        "CDM",
        "LM", "CM", "RM",
        "ST", "ST",
    ],

    "4-4-1-1": [
        "GK",
        "LB", "CB", "CB", "RB",
        "LM", "CM", "CM", "RM",
        "CAM",
        "ST",
    ],

    "4-5-1": [
        "GK",
        "LB", "CB", "CB", "RB",
        "LM", "CM", "CDM", "CM", "RM",
        "ST",
    ],

    "3-4-3": [
        "GK",
        "CB", "CB", "CB",
        "LWB", "CM", "CM", "RWB",
        "LW", "ST", "RW",
    ],

    "3-4-2-1": [
        "GK",
        "CB", "CB", "CB",
        "LWB", "CM", "CM", "RWB",
        "CAM", "CAM",
        "ST",
    ],

    "3-4-1-2": [
        "GK",
        "CB", "CB", "CB",
        "LWB", "CM", "CM", "RWB",
        "CAM",
        "ST", "ST",
    ],

    "3-5-2": [
        "GK",
        "CB", "CB", "CB",
        "LWB", "CM", "CDM", "CM", "RWB",
        "ST", "ST",
    ],

    "3-5-1-1": [
        "GK",
        "CB", "CB", "CB",
        "LWB", "CM", "CDM", "CM", "RWB",
        "CAM",
        "ST",
    ],

    "3-1-4-2": [
        "GK",
        "CB", "CB", "CB",
        "CDM",
        "LM", "CM", "CM", "RM",
        "ST", "ST",
    ],

    "3-2-4-1": [
        "GK",
        "CB", "CB", "CB",
        "CDM", "CDM",
        "LM", "CAM", "CAM", "RM",
        "ST",
    ],

    "3-3-1-3": [
        "GK",
        "CB", "CB", "CB",
        "LM", "CM", "RM",
        "CAM",
        "LW", "ST", "RW",
    ],

    "3-3-3-1": [
        "GK",
        "CB", "CB", "CB",
        "LWB", "CM", "RWB",
        "LW", "CAM", "RW",
        "ST",
    ],

    "5-3-2": [
        "GK",
        "LWB", "CB", "CB", "CB", "RWB",
        "CM", "CDM", "CM",
        "ST", "ST",
    ],

    "5-4-1": [
        "GK",
        "LWB", "CB", "CB", "CB", "RWB",
        "LM", "CM", "CM", "RM",
        "ST",
    ],
}


# =========================================================
# POSITION COMPATIBILITY
#
# 100 = natural position
# 80-95 = very compatible
# 60-79 = playable / reasonable adaptation
# <60 = increasingly unnatural
# =========================================================

POSITION_COMPATIBILITY = {
    "GK": {
        "GK": 100,
    },

    "CB": {
        "CB": 100,
        "CDM": 75,
        "LB": 55,
        "RB": 55,
        "LWB": 30,
        "RWB": 30,
    },

    "LB": {
        "LB": 100,
        "LWB": 92,
        "LM": 72,
        "CB": 55,
        "LW": 48,
        "RB": 30,
    },

    "RB": {
        "RB": 100,
        "RWB": 92,
        "RM": 72,
        "CB": 55,
        "RW": 48,
        "LB": 30,
    },

    "LWB": {
        "LWB": 100,
        "LB": 92,
        "LM": 85,
        "LW": 68,
        "CM": 42,
        "RWB": 30,
    },

    "RWB": {
        "RWB": 100,
        "RB": 92,
        "RM": 85,
        "RW": 68,
        "CM": 42,
        "LWB": 30,
    },

    "CDM": {
        "CDM": 100,
        "CM": 88,
        "CB": 75,
        "CAM": 45,
        "LM": 35,
        "RM": 35,
    },

    "CM": {
        "CM": 100,
        "CDM": 88,
        "CAM": 82,
        "LM": 65,
        "RM": 65,
    },

    "CAM": {
        "CAM": 100,
        "CM": 82,
        "LM": 78,
        "RM": 78,
        "LW": 75,
        "RW": 75,
        "ST": 55,
        "CDM": 40,
    },

    "LM": {
        "LM": 100,
        "LW": 90,
        "LWB": 80,
        "CAM": 72,
        "CM": 65,
        "LB": 62,
        "RM": 35,
    },

    "RM": {
        "RM": 100,
        "RW": 90,
        "RWB": 80,
        "CAM": 72,
        "CM": 65,
        "RB": 62,
        "LM": 35,
    },

    "LW": {
        "LW": 100,
        "LM": 90,
        "CAM": 75,
        "ST": 68,
        "LWB": 55,
        "RW": 45,
    },

    "RW": {
        "RW": 100,
        "RM": 90,
        "CAM": 75,
        "ST": 68,
        "RWB": 55,
        "LW": 45,
    },

    "ST": {
        "ST": 100,
        "LW": 68,
        "RW": 68,
        "CAM": 55,
        "LM": 45,
        "RM": 45,
    },

    # Side-neutral fallbacks used when the source data
    # identifies a role family but not a left/right side.
    "FB": {
        "LB": 95,
        "RB": 95,
        "LWB": 88,
        "RWB": 88,
        "LM": 60,
        "RM": 60,
        "CB": 55,
    },

    "W": {
        "LW": 95,
        "RW": 95,
        "LM": 88,
        "RM": 88,
        "CAM": 75,
        "ST": 65,
        "LWB": 45,
        "RWB": 45,
    },

    # Defensive fallbacks for records whose source only
    # provides a broad position.
    "DEF": {
        "CB": 85,
        "LB": 72,
        "RB": 72,
        "LWB": 62,
        "RWB": 62,
        "CDM": 55,
    },

    "MID": {
        "CM": 85,
        "CDM": 75,
        "CAM": 75,
        "LM": 70,
        "RM": 70,
    },

    "ATT": {
        "ST": 85,
        "LW": 75,
        "RW": 75,
        "CAM": 60,
    },
}


# =========================================================
# DATA
# =========================================================

def load_data():
    players = pd.read_csv(PLAYER_FILE)
    formations = pd.read_csv(FORMATION_FILE)

    try:
        verified = pd.read_csv(
            REALISM_FILE
        )[[
            "api_football_player_id",
            "verified_primary_position",
            "verified_secondary_position",
            "verified_position_source",
            "verified_position_confidence",
            "verified_position_history",
        ]].rename(columns={
            "api_football_player_id": "player_id"
        })
    except FileNotFoundError:
        verified = None

    if verified is not None:
        players = players.merge(
            verified,
            on="player_id",
            how="left",
        )
        has_verified_position = players[
            "verified_primary_position"
        ].notna()

        players.loc[
            has_verified_position,
            "primary_position",
        ] = players.loc[
            has_verified_position,
            "verified_primary_position",
        ]
        players.loc[
            has_verified_position,
            "secondary_position",
        ] = players.loc[
            has_verified_position,
            "verified_secondary_position",
        ]
        players.loc[
            has_verified_position,
            "position_source",
        ] = players.loc[
            has_verified_position,
            "verified_position_source",
        ]
        players.loc[
            has_verified_position,
            "position_confidence",
        ] = players.loc[
            has_verified_position,
            "verified_position_confidence",
        ]
        players.loc[
            has_verified_position,
            "position_history",
        ] = players.loc[
            has_verified_position,
            "verified_position_history",
        ].fillna("")

    return players, formations


# =========================================================
# FIND PLAYER
# =========================================================

def find_player(players, player_name):
    query = player_name.strip().lower()

    exact = players[
        players["name"].astype(str).str.lower() == query
    ]

    if len(exact) == 1:
        return exact.iloc[0]

    partial = players[
        players["name"]
        .astype(str)
        .str.lower()
        .str.contains(query, regex=False)
    ]

    if len(partial) == 1:
        return partial.iloc[0]

    if len(partial) > 1:
        print("\nMultiple players found:\n")

        print(
            partial[
                [
                    "name",
                    "primary_position",
                    "secondary_position",
                ]
            ].to_string(index=False)
        )

        raise SystemExit(
            "\nPlease enter a more specific player name."
        )

    raise SystemExit(
        f"\nPlayer not found: {player_name}"
    )

def find_player_by_id(players, player_id):
    match = players[
        players["player_id"] == player_id
    ]

    if len(match) == 1:
        return match.iloc[0]

    if len(match) > 1:
        raise SystemExit(
            f"\nMultiple position records found "
            f"for player_id: {player_id}"
        )

    raise SystemExit(
        f"\nPosition data not found "
        f"for player_id: {player_id}"
    )
# =========================================================
# FIND TEAM
# =========================================================

def find_team(formations, team_name):
    query = team_name.strip().lower()

    exact = formations[
        formations["team"].astype(str).str.lower() == query
    ]

    if len(exact) == 1:
        return exact.iloc[0]

    partial = formations[
        formations["team"]
        .astype(str)
        .str.lower()
        .str.contains(query, regex=False)
    ]

    if len(partial) == 1:
        return partial.iloc[0]

    if len(partial) > 1:
        print("\nMultiple teams found:\n")

        print(
            partial["team"].to_string(index=False)
        )

        raise SystemExit(
            "\nPlease enter a more specific team name."
        )

    raise SystemExit(
        f"\nTeam not found: {team_name}"
    )


# =========================================================
# PARSE PLAYER POSITION HISTORY
# Example:
# CAM:21 | LW:1
# =========================================================

def parse_position_history(history):
    positions = {}

    if pd.isna(history):
        return positions

    for part in str(history).split("|"):
        part = part.strip()

        if ":" not in part:
            continue

        position, starts = part.split(":", 1)

        position = position.strip()
        starts = starts.strip()

        try:
            starts = int(starts)
        except ValueError:
            continue

        positions[position] = starts

    return positions


# =========================================================
# PARSE TEAM FORMATION HISTORY
# Example:
# 4-3-3:24 | 4-2-3-1:14
# =========================================================

def parse_formation_history(history):
    formations = {}

    if pd.isna(history):
        return formations

    for part in str(history).split("|"):
        part = part.strip()

        if ":" not in part:
            continue

        formation, matches = part.split(":", 1)

        formation = formation.strip()
        matches = matches.strip()

        try:
            matches = int(matches)
        except ValueError:
            continue

        formations[formation] = matches

    return formations


def get_team_formation_options(team, limit=3):
    """Return the club's most-used supported formations."""
    history = parse_formation_history(
        team.get("formation_history")
    )
    ranked = sorted(
        history.items(),
        key=lambda item: item[1],
        reverse=True,
    )
    total_matches = sum(history.values())
    options = []

    for formation, matches in ranked:
        if formation not in FORMATION_ROLES:
            continue

        options.append({
            "formation": formation,
            "matches": int(matches),
            "usage_percentage": round(
                matches / max(total_matches, 1) * 100,
                1,
            ),
            "is_primary": (
                formation == team.get("primary_formation")
            ),
        })

        if len(options) >= max(1, int(limit)):
            break

    if not options:
        primary = team.get("primary_formation")

        if primary in FORMATION_ROLES:
            options.append({
                "formation": primary,
                "matches": int(
                    team.get("primary_matches", 0) or 0
                ),
                "usage_percentage": round(float(
                    team.get("primary_percentage", 100) or 100
                ), 1),
                "is_primary": True,
            })

    return options


# =========================================================
# POSITION -> ROLE COMPATIBILITY
# =========================================================

def compatibility(player_position, formation_role):
    if pd.isna(player_position):
        return 0

    player_position = str(player_position).strip()
    formation_role = str(formation_role).strip()

    if player_position == formation_role:
        return 100

    return POSITION_COMPATIBILITY.get(
        player_position,
        {}
    ).get(
        formation_role,
        0
    )


# =========================================================
# BEST ROLE IN A FORMATION
# =========================================================

def best_role_fit(player_position, formation):
    roles = FORMATION_ROLES.get(formation)

    if not roles:
        return 0, None

    best_score = -1
    best_role = None

    for role in roles:
        score = compatibility(
            player_position,
            role
        )

        if score > best_score:
            best_score = score
            best_role = role

    return best_score, best_role


# =========================================================
# PLAYER FIT TO ONE FORMATION
# =========================================================

def player_fit_to_formation(player, formation):
    primary = player["primary_position"]

    secondary = player.get(
        "secondary_position",
        None
    )

    confidence = pd.to_numeric(
        player.get("position_confidence", 100),
        errors="coerce"
    )

    if pd.isna(confidence):
        confidence = 100

    confidence = max(
        0,
        min(100, float(confidence))
    ) / 100


    # -----------------------------------------------------
    # Primary position
    # -----------------------------------------------------

    primary_fit, primary_role = best_role_fit(
        primary,
        formation
    )


    # -----------------------------------------------------
    # Secondary position
    # -----------------------------------------------------

    has_secondary = (
        not pd.isna(secondary)
        and str(secondary).strip() != ""
    )

    if has_secondary:
        secondary_fit, secondary_role = best_role_fit(
            secondary,
            formation
        )
    else:
        secondary_fit = primary_fit
        secondary_role = primary_role


    # -----------------------------------------------------
    # Full position history
    # -----------------------------------------------------

    history = parse_position_history(
        player.get("position_history")
    )

    total_history_starts = sum(history.values())

    if total_history_starts > 0:
        weighted_history_fit = 0

        for position, starts in history.items():
            score, _ = best_role_fit(
                position,
                formation
            )

            weighted_history_fit += (
                score * starts
            )

        history_fit = (
            weighted_history_fit
            / total_history_starts
        )

    else:
        history_fit = primary_fit


    # -----------------------------------------------------
    # Dynamic weighting
    #
    # High confidence:
    # primary role matters more.
    #
    # Lower confidence:
    # history matters more.
    # -----------------------------------------------------

    primary_weight = (
        0.45 + 0.25 * confidence
    )

    if has_secondary:
        secondary_weight = 0.15
    else:
        secondary_weight = 0

    history_weight = (
        1
        - primary_weight
        - secondary_weight
    )


    formation_fit = (
        primary_fit * primary_weight
        + secondary_fit * secondary_weight
        + history_fit * history_weight
    )

    formation_fit = round(
        max(0, min(100, formation_fit)),
        1
    )

    return {
        "formation": formation,
        "formation_fit": formation_fit,
        "primary_fit": round(primary_fit, 1),
        "primary_role": primary_role,
        "secondary_fit": round(secondary_fit, 1),
        "secondary_role": secondary_role,
        "history_fit": round(history_fit, 1),
    }


# =========================================================
# OVERALL POSITION FIT
# =========================================================

def calculate_position_fit(player, team):
    formation_history = parse_formation_history(
        team["formation_history"]
    )

    if not formation_history:
        raise SystemExit(
            "\nNo formation history found for this team."
        )

    total_matches = sum(
        formation_history.values()
    )

    details = []

    overall_score = 0

    for formation, matches in formation_history.items():
        if formation not in FORMATION_ROLES:
            print(
                f"\nWarning: unsupported formation "
                f"{formation}"
            )
            continue

        formation_result = player_fit_to_formation(
            player,
            formation
        )

        usage = (
            matches / total_matches
        )

        contribution = (
            formation_result["formation_fit"]
            * usage
        )

        formation_result["matches"] = matches

        formation_result["usage_percentage"] = round(
            usage * 100,
            1
        )

        formation_result["weighted_contribution"] = round(
            contribution,
            2
        )

        details.append(
            formation_result
        )

        overall_score += contribution

    return (
        round(overall_score, 1),
        pd.DataFrame(details)
    )


# =========================================================
# LABEL
# =========================================================

def position_fit_label(score):
    if score >= 90:
        return "Elite Position Fit"

    if score >= 80:
        return "Strong Position Fit"

    if score >= 70:
        return "Good Position Fit"

    if score >= 60:
        return "Moderate Position Fit"

    return "Low Position Fit"


# =========================================================
# DISPLAY
# =========================================================

def print_result(player, team, score, details):
    print("\n" + "=" * 82)

    print(
        "TRANSFIT AI - POSITION FIT ANALYSIS"
    )

    print("=" * 82)

    print(
        f"\nPlayer:              "
        f"{player['name']}"
    )

    print(
        f"Primary Position:    "
        f"{player['primary_position']}"
    )

    secondary = player.get(
        "secondary_position"
    )

    if pd.isna(secondary):
        secondary = "-"

    print(
        f"Secondary Position:  "
        f"{secondary}"
    )

    print(
        f"Position Confidence: "
        f"{player['position_confidence']}%"
    )

    print(
        f"Position History:    "
        f"{player['position_history']}"
    )

    print(
        f"Target Team:         "
        f"{team['team']}"
    )

    print(
        f"Primary Formation:   "
        f"{team['primary_formation']}"
    )

    print("\n" + "-" * 82)

    print(
        f"\nPOSITION FIT SCORE: "
        f"{score} / 100"
    )

    print(
        f"Classification: "
        f"{position_fit_label(score)}"
    )

    print("\n" + "-" * 82)

    display = details.copy()

    display = display.rename(
        columns={
            "formation": "Formation",
            "matches": "Matches",
            "usage_percentage": "Usage %",
            "formation_fit": "Fit",
            "primary_role": "Best Primary Role",
            "secondary_role": "Best Secondary Role",
            "weighted_contribution": "Contribution",
        }
    )

    print(
        "\n"
        + display[
            [
                "Formation",
                "Matches",
                "Usage %",
                "Fit",
                "Best Primary Role",
                "Best Secondary Role",
                "Contribution",
            ]
        ].to_string(index=False)
    )

    if not details.empty:
        best = details.loc[
            details["formation_fit"].idxmax()
        ]

        most_used = details.loc[
            details["usage_percentage"].idxmax()
        ]

        print("\n" + "-" * 82)

        print(
            "\nBest formation for player:"
        )

        print(
            f"{best['formation']} "
            f"({best['formation_fit']}/100)"
        )

        print(
            "\nFit in team's main formation:"
        )

        print(
            f"{most_used['formation']} "
            f"({most_used['formation_fit']}/100)"
        )

    print("\n" + "=" * 82)


# =========================================================
# MAIN
# =========================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "TransFit AI Position Fit Engine"
        )
    )

    parser.add_argument(
        "player",
        help="Player name"
    )

    parser.add_argument(
        "team",
        help="Target team"
    )

    args = parser.parse_args()

    players, formations = load_data()

    player = find_player(
        players,
        args.player
    )

    team = find_team(
        formations,
        args.team
    )

    score, details = calculate_position_fit(
        player,
        team
    )

    print_result(
        player,
        team,
        score,
        details
    )


if __name__ == "__main__":
    main()
