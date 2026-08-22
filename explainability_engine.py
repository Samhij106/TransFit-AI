import math


EXPLAINABILITY_VERSION = "TransFit XAI v1"
MODEL_VERSION = "TransFit V12 Explainable AI"


FACTOR_DEFINITIONS = {
    "tactical": {
        "label": "Tactical fit",
        "high": "The player's statistical style aligns with the target club's playing profile.",
        "low": "The playing-style match suggests a meaningful adaptation requirement.",
    },
    "position": {
        "label": "Role fit",
        "high": "The player is naturally suited to the selected role and formation.",
        "low": "The selected role is not a strong natural match for the player's position profile.",
    },
    "performance": {
        "label": "Role performance",
        "high": "Current production is strong when evaluated against the demands of this role.",
        "low": "Recent role-specific output is below the level expected from a priority target.",
    },
    "proven": {
        "label": "Proven level",
        "high": "Senior-level evidence and market calibration support the quality signal.",
        "low": "The player has less proven senior evidence than the strongest alternatives.",
    },
    "availability": {
        "label": "Availability",
        "high": "Minutes, starts and appearances provide a reliable evidence base.",
        "low": "Limited minutes or starts reduce confidence in the current performance sample.",
    },
    "potential": {
        "label": "Development upside",
        "high": "Age and performance trajectory leave meaningful development runway.",
        "low": "The model sees limited future-value upside from the age and trajectory profile.",
    },
    "squad_need": {
        "label": "Squad need",
        "high": "The target squad has a meaningful quality or depth opportunity in this role.",
        "low": "The target squad already has strong coverage in the selected role.",
    },
    "deal_feasibility": {
        "label": "Deal feasibility",
        "high": "Club stature, player level and market tier create a credible transfer path.",
        "low": "The sporting fit is weakened by a difficult club-status or market pathway.",
    },
    "league_strength": {
        "label": "League context",
        "high": "The current competition provides a strong level of proven context.",
        "low": "The step in competition level adds uncertainty to the projection.",
    },
}


ML_FEATURE_LABELS = {
    "age_at_transfer": "Age at transfer",
    "market_value_m_eur": "Market value",
    "appearances_before": "Pre-transfer appearances",
    "starts_before": "Pre-transfer starts",
    "minutes_before": "Pre-transfer minutes",
    "goals_before": "Pre-transfer goals",
    "assists_before": "Pre-transfer assists",
    "minutes_per_appearance_before": "Minutes per appearance",
    "start_share_before": "Starting share",
    "goal_involvement_per90_before": "Goal involvement per 90",
    "from_club_level": "Selling-club level",
    "to_club_level": "Target-club level",
    "club_level_step": "Club-level step",
    "from_league_strength": "Selling-league strength",
    "to_league_strength": "Target-league strength",
    "league_strength_step": "League-strength step",
    "same_competition": "Same-league move",
    "primary_position": "Position profile",
    "from_competition_id": "Selling competition",
    "to_competition_id": "Target competition",
}


def finite_number(value, default=None):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number):
        return default
    return number


def clamp(value, minimum=0.0, maximum=100.0):
    return max(minimum, min(maximum, float(value)))


def confidence_label(score):
    if score >= 78:
        return "high"
    if score >= 60:
        return "medium"
    return "low"


def verdict_label(score):
    if score >= 85:
        return "High-priority transfer fit"
    if score >= 75:
        return "Strong shortlist candidate"
    if score >= 65:
        return "Conditional transfer fit"
    return "Low-priority or unrealistic fit"


def factor_evidence(key, score, role=None, budget_status=None):
    definition = FACTOR_DEFINITIONS[key]
    evidence = definition["high"] if score >= 70 else definition["low"]
    if key == "position" and role:
        evidence = f"{evidence} Evaluated role: {role}."
    if key == "deal_feasibility" and budget_status == "stretch":
        evidence += " The estimated fee requires the permitted 15% budget stretch."
    if key == "deal_feasibility" and budget_status == "within_budget":
        evidence += " The estimated fee remains within the selected budget."
    return evidence


def build_factor_trace(scores, weights, role=None, budget_status=None):
    factors = []
    for key, definition in FACTOR_DEFINITIONS.items():
        score = finite_number(scores.get(key))
        weight = finite_number(weights.get(key), 0.0)
        if score is None:
            continue

        score = clamp(score)
        weight = max(0.0, weight)
        weighted_points = score * weight / 100
        impact_from_neutral = (score - 65.0) * weight / 100
        factors.append({
            "factor": key,
            "label": definition["label"],
            "score": round(score, 1),
            "weight": round(weight, 1),
            "weighted_points": round(weighted_points, 2),
            "impact_from_neutral": round(impact_from_neutral, 2),
            "direction": (
                "positive"
                if score >= 70
                else "risk"
                if score < 60
                else "neutral"
            ),
            "evidence": factor_evidence(
                key,
                score,
                role=role,
                budget_status=budget_status,
            ),
            "source": "role-aware expert engine",
        })

    positive = sorted(
        (factor for factor in factors if factor["score"] >= 70),
        key=lambda factor: (
            factor["impact_from_neutral"],
            factor["weighted_points"],
        ),
        reverse=True,
    )[:4]
    risks = sorted(
        (factor for factor in factors if factor["score"] < 70),
        key=lambda factor: (
            factor["impact_from_neutral"],
            factor["score"],
        ),
    )[:3]

    if not risks and factors:
        lowest = min(factors, key=lambda factor: factor["score"])
        risks = [{**lowest, "direction": "watch"}]

    return factors, positive, risks


def build_ml_drivers(ml_prediction):
    explanation = (ml_prediction or {}).get("local_explanation") or {}
    drivers = []
    for direction, key in (
        ("positive", "positive_drivers"),
        ("risk", "risk_drivers"),
    ):
        for driver in explanation.get(key, []):
            feature = str(driver.get("feature") or "unknown")
            effect = finite_number(driver.get("effect"), 0.0)
            drivers.append({
                "feature": feature,
                "label": ML_FEATURE_LABELS.get(
                    feature,
                    feature.replace("_", " ").title(),
                ),
                "effect": round(effect, 2),
                "direction": direction,
                "evidence": (
                    "Raises the historical success forecast versus the model's reference profile."
                    if direction == "positive"
                    else "Lowers the historical success forecast versus the model's reference profile."
                ),
                "source": "historical transfer-success model",
            })
    return drivers


def build_architecture_trace(
    expert_score,
    final_score,
    hybrid_weights,
    ml_prediction=None,
    ranker_prediction=None,
    transfer_feasibility=None,
):
    ml_available = ml_prediction is not None
    ranker_available = ranker_prediction is not None
    expert_weight = finite_number(
        hybrid_weights.get("expert_model"),
        100.0 if not ml_available else 70.0,
    )
    historical_weight = finite_number(
        hybrid_weights.get("historical_ml"),
        0.0 if not ml_available else 30.0,
    )
    ranker_weight = finite_number(
        hybrid_weights.get("club_role_ranker"),
        0.0,
    )

    components = [{
        "engine": "expert_model",
        "label": "Role-aware expert engine",
        "score": round(clamp(expert_score), 1),
        "weight": round(expert_weight, 1),
        "weighted_points": round(clamp(expert_score) * expert_weight / 100, 2),
        "available": True,
        "scope": "sporting fit, squad need and deal realism",
    }]

    if ml_available:
        historical_score = finite_number(
            ml_prediction.get("success_percentile"),
            expert_score,
        )
        components.append({
            "engine": "historical_ml",
            "label": "Historical success model",
            "score": round(clamp(historical_score), 1),
            "raw_forecast": finite_number(
                ml_prediction.get("success_forecast")
            ),
            "weight": round(historical_weight, 1),
            "weighted_points": round(
                clamp(historical_score) * historical_weight / 100,
                2,
            ),
            "available": True,
            "scope": "first-season outcome evidence from historical transfers",
        })
    else:
        components.append({
            "engine": "historical_ml",
            "label": "Historical success model",
            "score": None,
            "weight": 0.0,
            "weighted_points": 0.0,
            "available": False,
            "scope": "no reliable historical player identity match",
        })

    if ranker_available:
        ranker_score = finite_number(
            ranker_prediction.get("club_role_rank_score"),
            50.0,
        )
        components.append({
            "engine": "club_role_ranker",
            "label": "Club × role ranker",
            "score": round(clamp(ranker_score), 1),
            "weight": round(ranker_weight, 1),
            "weighted_points": round(
                clamp(ranker_score) * ranker_weight / 100,
                2,
            ),
            "available": True,
            "scope": "pairwise comparison against the eligible live candidate pool",
            "comparisons": ranker_prediction.get("comparisons"),
        })

    calculated = round(
        sum(component["weighted_points"] for component in components),
        1,
    )
    adjustments = []
    feasibility = transfer_feasibility or {}
    if not feasibility.get("eligible", True) and final_score <= 55:
        adjustments.append({
            "type": "realism_guardrail",
            "label": "Realism guardrail",
            "effect": round(final_score - calculated, 1),
            "reason": "An ineligible club-status or market pathway caps the final score at 55.",
        })
    elif abs(calculated - final_score) >= 0.2:
        adjustments.append({
            "type": "rounding_or_calibration",
            "label": "Final calibration",
            "effect": round(final_score - calculated, 1),
            "reason": "The reported score includes final model calibration and rounding.",
        })

    return {
        "components": components,
        "calculated_score": calculated,
        "reported_score": round(final_score, 1),
        "adjustments": adjustments,
        "formula": "weighted sum of available engines, followed by realism guardrails",
    }


def build_evidence_confidence(
    ml_prediction=None,
    ranker_prediction=None,
    performance_reliability=None,
    value_source=None,
    transfer_feasibility=None,
):
    score = 35.0
    reasons = []

    reliability = clamp(finite_number(performance_reliability, 60.0))
    score += reliability * 0.20
    reasons.append(
        f"Performance sample reliability contributes {round(reliability * 0.20, 1)} confidence points."
    )

    if value_source == "transfermarkt":
        score += 10
        reasons.append("Market value is matched to Transfermarkt evidence.")
    else:
        score += 4
        reasons.append("Market value uses the internal estimate rather than a direct match.")

    feasibility = transfer_feasibility or {}
    if feasibility.get("status") not in (None, "uncertain"):
        score += 5
        reasons.append("The transfer-realism engine resolved a clear market-path status.")

    if ml_prediction is not None:
        ml_confidence = ml_prediction.get("confidence", "low")
        score += 15 + {"high": 10, "medium": 6, "low": 2}.get(
            ml_confidence,
            2,
        )
        reasons.append(
            f"Historical ML is available with {ml_confidence} interval confidence."
        )
    else:
        reasons.append("Historical ML is unavailable for this player identity.")

    if ranker_prediction is not None:
        rank_confidence = ranker_prediction.get("confidence", "low")
        score += {"high": 5, "medium": 3, "low": 1}.get(
            rank_confidence,
            1,
        )
        reasons.append(
            f"The live-pool ranker has {rank_confidence} pairwise confidence."
        )

    score = round(clamp(score), 1)
    return {
        "score": score,
        "level": confidence_label(score),
        "meaning": "Evidence coverage and model certainty, not transfer probability.",
        "reasons": reasons,
    }


def build_transfer_explanation(
    *,
    player_name,
    current_team,
    target_team,
    role,
    scores,
    weights,
    final_score,
    expert_score,
    hybrid_weights,
    ml_prediction=None,
    ranker_prediction=None,
    transfer_feasibility=None,
    budget_status=None,
    value_source=None,
    performance_reliability=None,
    context="isolated_player_analysis",
):
    ml_prediction = ml_prediction if isinstance(ml_prediction, dict) else None
    ranker_prediction = (
        ranker_prediction if isinstance(ranker_prediction, dict) else None
    )
    transfer_feasibility = (
        transfer_feasibility
        if isinstance(transfer_feasibility, dict)
        else {}
    )
    hybrid_weights = (
        hybrid_weights if isinstance(hybrid_weights, dict) else {}
    )
    final_score = clamp(finite_number(final_score, 0.0))
    expert_score = clamp(finite_number(expert_score, final_score))
    factors, positives, risks = build_factor_trace(
        scores,
        weights,
        role=role,
        budget_status=budget_status,
    )
    ml_drivers = build_ml_drivers(ml_prediction)
    confidence = build_evidence_confidence(
        ml_prediction=ml_prediction,
        ranker_prediction=ranker_prediction,
        performance_reliability=performance_reliability,
        value_source=value_source,
        transfer_feasibility=transfer_feasibility,
    )
    architecture = build_architecture_trace(
        expert_score,
        final_score,
        hybrid_weights,
        ml_prediction=ml_prediction,
        ranker_prediction=ranker_prediction,
        transfer_feasibility=transfer_feasibility,
    )

    strength_labels = [factor["label"] for factor in positives[:2]]
    concern = risks[0]["label"] if risks else "no major model warning"
    strength_text = (
        " and ".join(strength_labels)
        if strength_labels
        else "balanced evidence across the evaluated dimensions"
    )
    summary = (
        f"{player_name} is evaluated for {target_team} from {current_team}. "
        f"The strongest evidence is {strength_text}; the main area to verify is {concern}."
    )

    limitations = [
        "Feature effects describe model behaviour and are not causal claims.",
        "The model does not currently include wages, contract demands, injuries or agent preference.",
        "Transfermarkt values are market estimates rather than guaranteed transfer fees.",
    ]
    if ranker_prediction is None:
        limitations.append(
            "The pairwise club-role ranker is only applied inside a live candidate pool, not to isolated analysis."
        )
    else:
        limitations.append(
            "The club-role rank score is relative to the current eligible pool and can change with filters or budget."
        )

    return {
        "version": EXPLAINABILITY_VERSION,
        "model_version": MODEL_VERSION,
        "context": context,
        "verdict": verdict_label(final_score),
        "summary": summary,
        "confidence": confidence,
        "decision_trace": architecture,
        "factor_trace": factors,
        "positive_factors": positives,
        "risk_factors": risks,
        "ml_drivers": ml_drivers,
        "limitations": limitations,
        "is_causal": False,
    }
