from transfer_fit_engine import (
    load_data as load_tactical_data,
    find_team as find_tactical_team,
)

from position_fit_engine import (
    load_data as load_position_data,
    find_team as find_formation_team,
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
    calculate_transfer_fit_v5,
    find_player_by_id,
    transfer_fit_label,
)

from candidate_ranking_engine import (
    rank_candidates,
)


# =========================================================
# ANALYZE ONE PLAYER -> TEAM
# =========================================================

def analyze_transfer(
    player_name,
    team_name,
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
    # V5
    # -----------------------------------------------------

    result = calculate_transfer_fit_v5(
        tactical_player,
        tactical_team,
        position_player,
        formation_team,
        performance_player,
        potential_player,
        squad,
    )

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

    return {
        "player": {
            "player_id": player_id,

            "name": tactical_player[
                "name"
            ],

            "current_team": tactical_player[
                "team"
            ],

            "age": float(
                result[
                    "potential_result"
                ]["age"]
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

            "primary_formation": formation_team[
                "primary_formation"
            ],

            "secondary_formation": formation_team[
                "secondary_formation"
            ],
        },

        "scores": {
            "final": result[
                "final_score"
            ],

            "classification": (
                transfer_fit_label(
                    result[
                        "final_score"
                    ]
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

            "potential": result[
                "potential_score"
            ],

            "squad_need": result[
                "squad_need_score"
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
    }


# =========================================================
# TEAM + ROLE -> TOP CANDIDATES
# =========================================================

def get_candidate_rankings(
    team_name,
    role,
    limit=10,
    min_minutes=450,
    min_role_fit=70,
):
    rankings, team, expected_slots = (
        rank_candidates(
            team_name,
            role.upper(),
            limit,
            min_minutes,
            min_role_fit,
        )
    )

    return {
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

        "candidates": rankings.to_dict(
            orient="records"
        ),
    }