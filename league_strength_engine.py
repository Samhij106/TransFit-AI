"""League-level calibration used by the TransFit scoring model.

The ordering is an explicit product assumption. It is deliberately a
moderate signal: league context should validate performance, not override
the player's role, output, tactical fit or transfer feasibility.
"""


LEAGUE_STRENGTH_SCORES = {
    "Premier League": 100.0,
    "La Liga": 94.0,
    "Serie A": 90.0,
    "Bundesliga": 86.0,
    "Ligue 1": 82.0,
}

LEAGUE_ALIASES = {
    "premier league": "Premier League",
    "epl": "Premier League",
    "la liga": "La Liga",
    "laliga": "La Liga",
    "serie a": "Serie A",
    "bundesliga": "Bundesliga",
    "ligue 1": "Ligue 1",
}

DEFAULT_LEAGUE_STRENGTH = 76.0


def normalize_league(league):
    key = " ".join(str(league or "").strip().lower().split())
    return LEAGUE_ALIASES.get(key)


def league_strength_score(league):
    canonical = normalize_league(league)

    if canonical is None:
        return DEFAULT_LEAGUE_STRENGTH

    return LEAGUE_STRENGTH_SCORES[canonical]


def league_strength_label(league):
    canonical = normalize_league(league)
    return canonical or "Other league"
