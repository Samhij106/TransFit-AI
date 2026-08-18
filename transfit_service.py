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

from league_config import LEAGUES

from transfer_value_engine import (
    BUDGET_TOLERANCE,
    assess_budget,
    resolve_transfer_value,
)

from realistic_data_engine import (
    find_realism_by_id,
    load_realism_profiles,
)


# =========================================================
# ANALYZE ONE PLAYER -> TEAM
# =========================================================

def analyze_transfer(
    player_name,
    team_name,
    player_id=None,
    budget_millions=None,
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

    transfer_value = resolve_transfer_value(
        player_id=player_id,
        performance_score=result[
            "performance_score"
        ],
        potential_score=result[
            "potential_score"
        ],
        age=result[
            "potential_result"
        ]["age"],
        minutes=performance_player[
            "minutes"
        ],
        league=performance_player.get(
            "league"
        ),
        position_group=performance_player[
            "position_group"
        ],
        position_source=position_player.get(
            "position_source"
        ),
    )

    budget_assessment = assess_budget(
        transfer_value[
            "estimated_value_m_eur"
        ],
        budget_millions,
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

            "league": performance_player.get(
                "league",
                None,
            ),

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
        },

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
):
    rankings, team, expected_slots = (
        rank_candidates(
            team_name,
            role.upper(),
            limit,
            min_minutes,
            min_role_fit,
            budget_millions,
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
