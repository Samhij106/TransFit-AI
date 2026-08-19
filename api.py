import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from transfit_service import (
    analyze_transfer,
    compare_players,
    get_candidate_rankings,
    get_club_catalog,
    search_players,
    get_team_profile,
)


app = FastAPI(
    title="TransFit AI API",
    description="AI-powered football transfer fit analysis API",
    version="1.0.0",
)


# =========================================================
# CORS
# =========================================================

local_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
deployed_origins = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "",
    ).split(",")
    if origin.strip()
]
allowed_origins = list(dict.fromkeys(
    local_origins + deployed_origins
))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/")
def root():
    return {
        "app": "TransFit AI",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok",
    }


@app.get("/api/clubs")
def clubs():
    return get_club_catalog()


# =========================================================
# PLAYER SEARCH
# =========================================================

@app.get("/api/players")
def players(
    q: str = "",
    limit: int = 12,
    team: str | None = None,
    position: str | None = None,
):
    try:
        return search_players(
            query=q,
            limit=limit,
            target_team=team,
            position=position,
        )

    except (SystemExit, ValueError) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


# =========================================================
# PLAYER COMPARISON
# =========================================================

@app.get("/api/compare")
def compare(
    team: str,
    player_ids: str,
    budget_millions: float | None = None,
):
    try:
        ids = [
            int(value.strip())
            for value in player_ids.split(",")
            if value.strip()
        ]

        return compare_players(
            team_name=team,
            player_ids=ids,
            budget_millions=budget_millions,
        )

    except (SystemExit, ValueError) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

# =========================================================
# TEAM PROFILE
# =========================================================

@app.get("/api/team")
def team_profile(
    team: str,
):
    try:
        return get_team_profile(
            team
        )

    except (SystemExit, ValueError) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )
    
# =========================================================
# TRANSFER ANALYSIS
# =========================================================

@app.get("/api/analyze")
def analyze(
    player: str,
    team: str,
    player_id: int | None = None,
    budget_millions: float | None = None,
):
    try:
        return analyze_transfer(
            player,
            team,
            player_id=player_id,
            budget_millions=budget_millions,
        )

    except (SystemExit, ValueError) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


# =========================================================
# CANDIDATE RANKINGS
# =========================================================

@app.get("/api/rankings")
def rankings(
    team: str,
    role: str,
    limit: int = 10,
    min_minutes: int = 450,
    min_role_fit: float = 80,
    budget_millions: float | None = None,
):
    try:
        return get_candidate_rankings(
            team_name=team,
            role=role,
            limit=limit,
            min_minutes=min_minutes,
            min_role_fit=min_role_fit,
            budget_millions=budget_millions,
        )

    except (SystemExit, ValueError) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )
