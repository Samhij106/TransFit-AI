MODEL_VERSION = "transfer-success-hgb-v1"

BIG_FIVE_COMPETITIONS = (
    "GB1",
    "ES1",
    "IT1",
    "L1",
    "FR1",
)

LEAGUE_STRENGTH = {
    "GB1": 100.0,
    "ES1": 92.0,
    "IT1": 86.0,
    "L1": 82.0,
    "FR1": 76.0,
}

NUMERIC_FEATURES = [
    "age_at_transfer",
    "market_value_m_eur",
    "market_value_trend_180d_pct",
    "pre_appearances",
    "pre_starts",
    "pre_minutes",
    "pre_goals",
    "pre_assists",
    "pre_goal_assist_per90",
    "pre_minutes_share",
    "pre_start_share",
    "from_points_per_game",
    "to_points_per_game",
    "from_goal_difference_per_game",
    "to_goal_difference_per_game",
    "league_strength_gap",
    "previous_transfers_3y",
    "is_cross_border",
    "is_winter_window",
]

CATEGORICAL_FEATURES = [
    "broad_position",
    "sub_position",
    "from_competition_id",
    "to_competition_id",
    "to_club_id",
]

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET = "success_score"

TRAIN_END = "2023-06-30"
VALIDATION_END = "2024-06-30"
SUCCESS_THRESHOLD = 60.0
