import unicodedata
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from transfer_fit_engine import (
    load_data as load_tactical_data,
    find_team as find_tactical_team,
)

from position_fit_engine import (
    apply_selected_formation,
    load_data as load_position_data,
    find_team as find_formation_team,
    get_team_formation_options,
)

from age_potential_engine import (
    prepare_data as prepare_potential_data,
)

from squad_need_engine import (
    load_data as load_squad_data,
    prepare_performance_data,
    resolve_candidate,
    build_team_squad,
)

from transfer_fit_v5 import (
    SCORE_VERSION,
    SCORE_WEIGHTS,
    calculate_transfer_fit_v5,
    find_player_by_id,
    transfer_fit_label,
)

from candidate_ranking_engine import (
    rank_candidates,
)

from league_config import LEAGUES

from transfer_value_engine import (
    BUDGET_TOLERANCE,
    assess_budget,
    load_market_values,
)

from realistic_data_engine import (
    find_realism_by_id,
    load_realism_profiles,
)
from ml.transfer_success_engine import (
    HYBRID_EXPERT_WEIGHT,
    HYBRID_ML_WEIGHT,
    HYBRID_SCORE_VERSION,
    build_feature_row,
    hybrid_score,
    hybrid_weight_payload,
    predict_feature_rows,
)
from explainability_engine import (
    EXPLAINABILITY_VERSION,
    build_transfer_explanation,
)


_PLAYER_SEARCH_CATALOG = None


def normalize_search_text(value):
    normalized = unicodedata.normalize(
        "NFKD",
        str(value or ""),
    )
    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(
            character
        )
    )

    return " ".join(
        normalized.lower().split()
    )


def load_player_search_catalog():
    global _PLAYER_SEARCH_CATALOG

    if _PLAYER_SEARCH_CATALOG is not None:
        return _PLAYER_SEARCH_CATALOG

    performance_players = (
        prepare_performance_data()
    )
    position_players, _ = load_position_data()

    positions = position_players[[
        "player_id",
        "primary_position",
        "secondary_position",
        "position_source",
    ]].drop_duplicates(
        subset=["player_id"],
        keep="first",
    )

    players = performance_players.drop(
        columns=[
            "primary_position",
            "secondary_position",
            "position_source",
        ],
        errors="ignore",
    ).merge(
        positions,
        on="player_id",
        how="left",
    )
    players = players[
        players["position_group"] != "GK"
    ].copy()
    players = players.drop_duplicates(
        subset=["player_id"],
        keep="first",
    )

    market_values = load_market_values()
    players["market_value_m_eur"] = players[
        "player_id"
    ].map(
        lambda player_id: market_values.get(
            int(player_id),
            {},
        ).get("market_value_m_eur")
    )
    players["value_source"] = players[
        "player_id"
    ].map(
        lambda player_id: market_values.get(
            int(player_id),
            {},
        ).get("value_source")
    )
    players["value_updated_at"] = players[
        "player_id"
    ].map(
        lambda player_id: market_values.get(
            int(player_id),
            {},
        ).get("value_updated_at")
    )
    players["normalized_name"] = players[
        "name"
    ].map(normalize_search_text)
    players["normalized_team"] = players[
        "team"
    ].map(normalize_search_text)

    _PLAYER_SEARCH_CATALOG = players
    return _PLAYER_SEARCH_CATALOG


def search_players(
    query="",
    limit=12,
    target_team=None,
    position=None,
):
    players = load_player_search_catalog().copy()
    normalized_query = normalize_search_text(
        query
    )
    normalized_target = normalize_search_text(
        target_team
    )

    if normalized_target:
        players = players[
            ~players["normalized_team"].map(
                lambda teams: normalized_target
                in {
                    normalize_search_text(team)
                    for team in str(teams).split(" | ")
                }
            )
        ].copy()

    if position:
        players = players[
            players["primary_position"]
            .astype(str)
            .str.upper()
            == str(position).upper()
        ].copy()

    if normalized_query:
        name_match = players[
            "normalized_name"
        ].str.contains(
            normalized_query,
            regex=False,
        )
        team_match = players[
            "normalized_team"
        ].str.contains(
            normalized_query,
            regex=False,
        )
        players = players[
            name_match | team_match
        ].copy()

        if players.empty:
            return {
                "query": query,
                "target_team": target_team,
                "count": 0,
                "players": [],
            }

        def match_rank(row):
            name = row["normalized_name"]
            team = row["normalized_team"]

            if name == normalized_query:
                return 0
            if name.startswith(
                normalized_query
            ):
                return 1
            if any(
                part.startswith(
                    normalized_query
                )
                for part in name.split()
            ):
                return 2
            if normalized_query in name:
                return 3
            if team.startswith(
                normalized_query
            ):
                return 4
            return 5

        players["match_rank"] = players.apply(
            match_rank,
            axis=1,
        )
    else:
        players["match_rank"] = 6

    players["market_value_sort"] = (
        pd.to_numeric(
            players["market_value_m_eur"],
            errors="coerce",
        ).fillna(-1)
    )
    players = players.sort_values(
        [
            "match_rank",
            "market_value_sort",
            "minutes",
            "name",
        ],
        ascending=[True, False, False, True],
    ).head(
        max(1, min(int(limit), 30))
    )

    results = []

    for _, player in players.iterrows():
        def optional_value(value):
            if value is None or pd.isna(value):
                return None

            return value

        secondary_position = player.get(
            "secondary_position"
        )
        market_value = player.get(
            "market_value_m_eur"
        )
        age = player.get("age")

        results.append({
            "player_id": int(
                player["player_id"]
            ),
            "name": player["name"],
            "current_team": player["team"],
            "league": optional_value(
                player.get("league")
            ),
            "age": (
                None
                if pd.isna(age)
                else float(age)
            ),
            "nationality": optional_value(
                player.get("nationality")
            ),
            "photo": (
                None
                if pd.isna(player.get("photo"))
                else player.get("photo")
            ),
            "primary_position": optional_value(
                player.get("primary_position")
            ),
            "secondary_position": (
                None
                if pd.isna(secondary_position)
                else secondary_position
            ),
            "position_source": optional_value(
                player.get("position_source")
            ),
            "minutes": int(float(
                player.get("minutes", 0)
            )),
            "market_value_m_eur": (
                None
                if pd.isna(market_value)
                else float(market_value)
            ),
            "value_source": optional_value(
                player.get("value_source")
            ),
            "value_updated_at": optional_value(
                player.get("value_updated_at")
            ),
        })

    return {
        "query": query,
        "target_team": target_team,
        "count": len(results),
        "players": results,
    }


# =========================================================
# ANALYZE ONE PLAYER -> TEAM
# =========================================================

def analyze_transfer(
    player_name,
    team_name,
    player_id=None,
    budget_millions=None,
    formation=None,
):
    # -----------------------------------------------------
    # Position / formation
    # -----------------------------------------------------

    (
        position_players,
        formation_teams,
    ) = load_position_data()

    formation_team = find_formation_team(
        formation_teams,
        team_name,
    )

    # -----------------------------------------------------
    # Performance
    # -----------------------------------------------------

    performance_players = (
        prepare_performance_data()
    )

    (
        performance_player,
        position_player,
    ) = resolve_candidate(
        performance_players,
        position_players,
        player_name,
        player_id=player_id,
    )

    player_id = int(
        performance_player["player_id"]
    )

    if (
        performance_player["position_group"]
        == "GK"
    ):
        raise ValueError(
            "Goalkeeper Transfer Fit "
            "is not supported yet."
        )

    # -----------------------------------------------------
    # Tactical
    # -----------------------------------------------------

    (
        tactical_players,
        tactical_teams,
    ) = load_tactical_data()

    tactical_player = find_player_by_id(
        tactical_players,
        player_id,
        "Tactical",
    )

    tactical_team = find_tactical_team(
        tactical_teams,
        team_name,
    )

    # -----------------------------------------------------
    # Potential
    # -----------------------------------------------------

    potential_players = (
        prepare_potential_data()
    )

    potential_player = find_player_by_id(
        potential_players,
        player_id,
        "Potential",
    )
    formation_team = apply_selected_formation(
        formation_team,
        formation=formation,
        limit=2,
    )

    realism_player = find_realism_by_id(
        load_realism_profiles(),
        player_id,
    )

    # -----------------------------------------------------
    # Squad
    # -----------------------------------------------------

    (
        raw_squad,
        _,
        _,
    ) = load_squad_data()

    squad = build_team_squad(
        raw_squad,
        position_players,
        performance_players,
        formation_team["team"],
        player_id,
    )

    # -----------------------------------------------------
    # V6 (legacy function name retained for compatibility)
    # -----------------------------------------------------

    result = calculate_transfer_fit_v5(
        tactical_player,
        tactical_team,
        position_player,
        formation_team,
        performance_player,
        potential_player,
        squad,
        realism_player,
    )

    transfer_value = result["transfer_value"]

    ml_feature_row = build_feature_row(
        transfermarkt_player_id=transfer_value.get(
            "transfermarkt_player_id"
        ),
        current_team=tactical_player["team"],
        target_team=formation_team["team"],
        current_league=performance_player.get("league"),
        target_league=formation_team["league"],
        age=result["potential_result"]["age"],
        market_value_m_eur=transfer_value[
            "estimated_value_m_eur"
        ],
        appearances=result["realism_details"][
            "current_appearances"
        ],
        starts=result["realism_details"]["current_starts"],
        minutes=result["realism_details"]["current_minutes"],
        goals=result["realism_details"]["current_goals"],
        assists=result["realism_details"]["current_assists"],
        primary_position=position_player["primary_position"],
    )
    ml_prediction = (
        None
        if ml_feature_row is None
        else predict_feature_rows(
            [ml_feature_row],
            include_explanations=True,
        )[0]
    )
    expert_score = float(result["final_score"])
    result["expert_score"] = round(expert_score, 1)
    result["ml_prediction"] = ml_prediction
    result["final_score"] = hybrid_score(
        expert_score,
        ml_prediction,
    )
    if not result["transfer_feasibility"]["eligible"]:
        result["final_score"] = min(result["final_score"], 55.0)

    budget_assessment = assess_budget(
        transfer_value[
            "estimated_value_m_eur"
        ],
        budget_millions,
    )
    transfer_feasibility = result["transfer_feasibility"]

    # =====================================================
    # EXPLANATIONS
    # =====================================================

    tactical_details = result[
        "tactical_details"
    ]

    strongest_tactical = tactical_details.loc[
        tactical_details[
            "similarity"
        ].idxmax()
    ]

    weakest_tactical = tactical_details.loc[
        tactical_details[
            "similarity"
        ].idxmin()
    ]

    performance_details = result[
        "performance_details"
    ]

    strongest_performance = (
        performance_details.loc[
            performance_details[
                "percentile"
            ].idxmax()
        ]
    )

    weakest_performance = (
        performance_details.loc[
            performance_details[
                "percentile"
            ].idxmin()
        ]
    )

    position_details = result[
        "position_details"
    ]

    best_formation = None
    main_formation_fit = None

    if not position_details.empty:

        best = position_details.loc[
            position_details[
                "formation_fit"
            ].idxmax()
        ]

        main = position_details.loc[
            position_details[
                "usage_percentage"
            ].idxmax()
        ]

        best_formation = {
            "formation": best[
                "formation"
            ],
            "fit": float(
                best["formation_fit"]
            ),
        }

        main_formation_fit = {
            "formation": main[
                "formation"
            ],
            "fit": float(
                main["formation_fit"]
            ),
        }

    # =====================================================
    # CLEAN RESPONSE FOR WEB / API
    # =====================================================

    response = {
        "player": {
            "player_id": player_id,

            "name": tactical_player[
                "name"
            ],

            "current_team": tactical_player[
                "team"
            ],

            "league": performance_player.get(
                "league",
                None,
            ),

            "age": (
                None
                if pd.isna(result[
                    "potential_result"
                ]["age"])
                else float(result[
                    "potential_result"
                ]["age"])
            ),

            "nationality": tactical_player.get(
                "nationality",
                None,
            ),

            "photo": tactical_player.get(
                "photo",
                None,
            ),

            "primary_position": position_player[
                "primary_position"
            ],

            "position_source": position_player.get(
                "position_source",
                None,
            ),

            "secondary_position": (
                None
                if str(
                    position_player[
                        "secondary_position"
                    ]
                ) == "nan"
                else position_player[
                    "secondary_position"
                ]
            ),
        },

        "target_team": {
            "name": tactical_team[
                "team"
            ],

            "league": formation_team[
                "league"
            ],

            "primary_formation": formation_team[
                "primary_formation"
            ],

            "secondary_formation": formation_team[
                "secondary_formation"
            ],

            "selected_formation": formation_team[
                "selected_formation"
            ],
        },

        "scores": {
            "version": (
                HYBRID_SCORE_VERSION
                if ml_prediction is not None
                else result.get("score_version", SCORE_VERSION)
            ),

            "hybrid_version": (
                HYBRID_SCORE_VERSION
                if ml_prediction is not None
                else None
            ),

            "weights": result.get(
                "score_weights",
                SCORE_WEIGHTS,
            ),

            "final": result[
                "final_score"
            ],

            "expert": result["expert_score"],

            "ml_success_forecast": (
                None
                if ml_prediction is None
                else ml_prediction["success_forecast"]
            ),

            "ml_success_percentile": (
                None
                if ml_prediction is None
                else ml_prediction["success_percentile"]
            ),

            "hybrid_weights": hybrid_weight_payload(),

            "classification": (
                "Unrealistic Transfer"
                if not transfer_feasibility["eligible"]
                else transfer_fit_label(
                    result["final_score"]
                )
            ),

            "tactical": result[
                "tactical_score"
            ],

            "position": result[
                "position_score"
            ],

            "performance": result[
                "performance_score"
            ],

            "league_performance": result[
                "league_performance_score"
            ],

            "production": result[
                "production_score"
            ],

            "proven": result[
                "proven_score"
            ],

            "availability": result[
                "availability_score"
            ],

            "potential": result[
                "potential_score"
            ],

            "squad_need": result[
                "squad_need_score"
            ],

            "deal_feasibility": result[
                "deal_feasibility_score"
            ],

            "league_strength": result[
                "league_strength_score"
            ],
        },

        "tactical": {
            "strongest_alignment": {
                "metric": strongest_tactical[
                    "metric"
                ],

                "score": float(
                    strongest_tactical[
                        "similarity"
                    ]
                ),
            },

            "biggest_mismatch": {
                "metric": weakest_tactical[
                    "metric"
                ],

                "score": float(
                    weakest_tactical[
                        "similarity"
                    ]
                ),
            },

            "metrics": (
                tactical_details
                .to_dict(
                    orient="records"
                )
            ),
        },

        "position": {
            "best_formation": (
                best_formation
            ),

            "main_formation": (
                main_formation_fit
            ),

            "formation_details": (
                position_details
                .to_dict(
                    orient="records"
                )
            ),
        },

        "performance": {
            "league_score": result[
                "league_performance_score"
            ],

            "production_score": result[
                "production_score"
            ],

            "blended_score": result[
                "performance_score"
            ],

            "reliability": result[
                "performance_reliability"
            ],

            "strongest_area": {
                "metric": (
                    strongest_performance[
                        "metric"
                    ]
                ),

                "percentile": float(
                    strongest_performance[
                        "percentile"
                    ]
                ),
            },

            "weakest_area": {
                "metric": (
                    weakest_performance[
                        "metric"
                    ]
                ),

                "percentile": float(
                    weakest_performance[
                        "percentile"
                    ]
                ),
            },

            "metrics": (
                performance_details
                .to_dict(
                    orient="records"
                )
            ),
        },

        "potential": {
            "development_runway": (
                result[
                    "potential_result"
                ][
                    "development_runway"
                ]
            ),

            "performance_for_age": (
                result[
                    "potential_result"
                ][
                    "performance_for_age"
                ]
            ),
        },

        "squad_need": {
            "score": result[
                "squad_best"
            ][
                "squad_need"
            ],

            "best_role": result[
                "squad_best"
            ][
                "role"
            ],

            "formation_demand": result[
                "squad_best"
            ][
                "formation_demand"
            ],

            "depth_need": result[
                "squad_best"
            ][
                "depth_need"
            ],

            "quality_need": result[
                "squad_best"
            ][
                "quality_need"
            ],

            "upgrade_opportunity": result[
                "squad_best"
            ][
                "upgrade_opportunity"
            ],
        },

        "realism": {
            **result["realism_details"],
            "league_performance_score": result[
                "league_performance_score"
            ],
            "blended_performance_score": result[
                "performance_score"
            ],
            "production_score": result[
                "production_score"
            ],
            "proven_score": result[
                "proven_score"
            ],
            "availability_score": result[
                "availability_score"
            ],
            "transfer_feasibility": transfer_feasibility,
            "sporting_fit_score": result[
                "sporting_fit_score"
            ],
        },

        "machine_learning": ml_prediction,

        "transfer_value": {
            **transfer_value,
            **budget_assessment,
            "selected_budget_m_eur": (
                None
                if budget_millions is None
                else float(budget_millions)
            ),
            "tolerance_percentage": (
                BUDGET_TOLERANCE * 100
            ),
        },
    }

    response["explainability"] = build_transfer_explanation(
        player_name=response["player"]["name"],
        current_team=response["player"]["current_team"],
        target_team=response["target_team"]["name"],
        role=(
            response["squad_need"].get("best_role")
            or response["player"].get("primary_position")
        ),
        scores={
            "tactical": response["scores"].get("tactical"),
            "position": response["scores"].get("position"),
            "performance": response["scores"].get("performance"),
            "proven": response["scores"].get("proven"),
            "availability": response["scores"].get("availability"),
            "potential": response["scores"].get("potential"),
            "squad_need": response["scores"].get("squad_need"),
            "deal_feasibility": response["scores"].get(
                "deal_feasibility"
            ),
            "league_strength": response["scores"].get(
                "league_strength"
            ),
        },
        weights=response["scores"]["weights"],
        final_score=response["scores"]["final"],
        expert_score=response["scores"]["expert"],
        hybrid_weights=response["scores"]["hybrid_weights"],
        ml_prediction=ml_prediction,
        transfer_feasibility=transfer_feasibility,
        budget_status=response["transfer_value"].get("budget_status"),
        value_source=response["transfer_value"].get("value_source"),
        performance_reliability=response["performance"].get(
            "reliability"
        ),
    )
    return response


# =========================================================
# TEAM + ROLE -> TOP CANDIDATES
# =========================================================

def get_candidate_rankings(
    team_name,
    role,
    limit=10,
    min_minutes=450,
    min_role_fit=80,
    budget_millions=None,
    formation=None,
):
    rankings, team, expected_slots = (
        rank_candidates(
            team_name,
            role.upper(),
            limit,
            min_minutes,
            min_role_fit,
            budget_millions,
            formation=formation,
        )
    )

    return {
        "scoring_model": {
            "version": HYBRID_SCORE_VERSION,
            "explainability_version": EXPLAINABILITY_VERSION,
            "weights": SCORE_WEIGHTS,
            "hybrid_weights": hybrid_weight_payload({}),
        },

        "team": team[
            "team"
        ],

        "role": role.upper(),

        "primary_formation": team[
            "primary_formation"
        ],

        "expected_slots": float(
            expected_slots
        ),

        "budget": {
            "selected_m_eur": (
                None
                if budget_millions is None
                else float(budget_millions)
            ),
            "tolerance_percentage": (
                BUDGET_TOLERANCE * 100
            ),
            "maximum_m_eur": (
                None
                if budget_millions is None
                else round(
                    float(budget_millions)
                    * (1 + BUDGET_TOLERANCE),
                    1,
                )
            ),
        },

        "candidates": rankings.to_dict(
            orient="records"
        ),
    }
def get_team_profile(team_name):
    (
        position_players,
        formation_teams,
    ) = load_position_data()

    team = find_formation_team(
        formation_teams,
        team_name,
    )

    return {
        "team_id": int(team["team_id"]),
        "team": team["team"],
        "league_id": int(team["league_id"]),
        "league": team["league"],
        "primary_formation": team["primary_formation"],
        "primary_percentage": float(
            team["primary_percentage"]
        ),
        "secondary_formation": team["secondary_formation"],
        "secondary_percentage": float(
            team["secondary_percentage"]
        ),
        "formation_history": team["formation_history"],
        "formation_options": get_team_formation_options(
            team,
            limit=2,
        ),
    }


# =========================================================
# PLAYER COMPARISON
# =========================================================

def compare_players(
    team_name,
    player_ids,
    budget_millions=None,
    formation=None,
):
    unique_ids = []

    for player_id in player_ids:
        player_id = int(player_id)

        if player_id not in unique_ids:
            unique_ids.append(player_id)

    if not 2 <= len(unique_ids) <= 4:
        raise ValueError(
            "Select between 2 and 4 unique players."
        )

    catalog = load_player_search_catalog()
    selected_players = []

    for player_id in unique_ids:
        match = catalog[
            catalog["player_id"] == player_id
        ]

        if len(match) != 1:
            raise ValueError(
                f"Player profile not found: {player_id}"
            )

        player = match.iloc[0]
        current_teams = {
            team.strip()
            for team in str(player["team"]).split("|")
        }

        if team_name in current_teams:
            raise ValueError(
                f"{player['name']} already plays for "
                f"{team_name}."
            )

        selected_players.append({
            "player_id": player_id,
            "name": player["name"],
        })

    def analyze_selected(player):
        return analyze_transfer(
            player["name"],
            team_name,
            player_id=player["player_id"],
            budget_millions=budget_millions,
            formation=formation,
        )

    with ThreadPoolExecutor(
        max_workers=len(selected_players)
    ) as executor:
        reports = list(
            executor.map(
                analyze_selected,
                selected_players,
            )
        )

    reports.sort(
        key=lambda report: report["scores"]["final"],
        reverse=True,
    )

    best_score = reports[0]["scores"]["final"]

    for rank, report in enumerate(reports, start=1):
        report["comparison_rank"] = rank
        report["score_gap_to_best"] = round(
            best_score - report["scores"]["final"],
            1,
        )

    metric_keys = [
        "expert",
        "ml_success_percentile",
        "tactical",
        "position",
        "performance",
        "proven",
        "availability",
        "potential",
        "squad_need",
        "deal_feasibility",
        "league_strength",
    ]
    dimension_leaders = {}

    for metric in metric_keys:
        eligible_reports = [
            report
            for report in reports
            if report["scores"].get(metric) is not None
        ]
        if not eligible_reports:
            continue
        leader = max(
            eligible_reports,
            key=lambda report: report["scores"][metric],
        )
        dimension_leaders[metric] = {
            "player_id": leader["player"]["player_id"],
            "name": leader["player"]["name"],
            "score": leader["scores"][metric],
        }

    decisive_factors = []

    if len(reports) > 1:
        winner = reports[0]
        runner_up = reports[1]
        weights = winner["scores"]["weights"]

        weight_keys = {
            "tactical": "tactical",
            "position": "position",
            "performance": "performance",
            "proven": "proven",
            "availability": "availability",
            "potential": "potential",
            "squad_need": "squad_need",
            "deal_feasibility": "deal_feasibility",
            "league_strength": "league_strength",
        }

        for metric, weight_key in weight_keys.items():
            raw_delta = (
                winner["scores"][metric]
                - runner_up["scores"][metric]
            )
            weighted_delta = (
                raw_delta
                * float(weights[weight_key])
                / 100
                * HYBRID_EXPERT_WEIGHT
            )

            decisive_factors.append({
                "metric": metric,
                "winner_score": winner["scores"][metric],
                "runner_up_score": runner_up["scores"][metric],
                "raw_delta": round(raw_delta, 1),
                "weighted_delta": round(weighted_delta, 2),
            })

        winner_ml = winner["scores"].get(
            "ml_success_percentile"
        )
        runner_up_ml = runner_up["scores"].get(
            "ml_success_percentile"
        )
        if winner_ml is not None and runner_up_ml is not None:
            raw_delta = winner_ml - runner_up_ml
            decisive_factors.append({
                "metric": "historical_ml",
                "winner_score": winner_ml,
                "runner_up_score": runner_up_ml,
                "raw_delta": round(raw_delta, 1),
                "weighted_delta": round(
                    raw_delta * HYBRID_ML_WEIGHT,
                    2,
                ),
            })

        decisive_factors.sort(
            key=lambda factor: factor["weighted_delta"],
            reverse=True,
        )
        decisive_factors = [
            factor
            for factor in decisive_factors
            if factor["weighted_delta"] > 0
        ]

    return {
        "target_team": reports[0]["target_team"],
        "scoring_model": {
            "version": HYBRID_SCORE_VERSION,
            "explainability_version": EXPLAINABILITY_VERSION,
            "weights": SCORE_WEIGHTS,
            "hybrid_weights": hybrid_weight_payload(),
        },
        "selected_budget_m_eur": (
            None
            if budget_millions is None
            else float(budget_millions)
        ),
        "player_count": len(reports),
        "winner": {
            "player_id": reports[0]["player"]["player_id"],
            "name": reports[0]["player"]["name"],
            "score": reports[0]["scores"]["final"],
        },
        "dimension_leaders": dimension_leaders,
        "decisive_factors": decisive_factors[:3],
        "players": reports,
    }


def get_club_catalog():
    (
        _,
        formation_teams,
    ) = load_position_data()

    league_by_id = {
        league["id"]: league
        for league in LEAGUES
    }

    catalog = []

    for league_id, clubs in (
        formation_teams.groupby("league_id")
    ):
        league_id = int(league_id)
        config = league_by_id.get(
            league_id,
            {},
        )

        club_rows = []

        for _, club in clubs.sort_values(
            "team"
        ).iterrows():
            club_rows.append({
                "team_id": int(
                    club["team_id"]
                ),
                "name": club["team"],
                "primary_formation": club[
                    "primary_formation"
                ],
            })

        catalog.append({
            "league_id": league_id,
            "key": config.get(
                "key",
                str(league_id),
            ),
            "name": config.get(
                "name",
                clubs.iloc[0]["league"],
            ),
            "country": config.get(
                "country"
            ),
            "club_count": len(club_rows),
            "clubs": club_rows,
        })

    configured_order = {
        league["id"]: index
        for index, league in enumerate(
            LEAGUES
        )
    }

    catalog.sort(
        key=lambda league: configured_order.get(
            league["league_id"],
            999,
        )
    )

    return {
        "leagues": catalog,
        "total_clubs": sum(
            league["club_count"]
            for league in catalog
        ),
    }
