from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from transfit_service import (
    analyze_transfer,
    get_candidate_rankings,
    get_club_catalog,
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    ],
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
