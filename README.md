# TransFit AI

AI-powered football transfer fit analysis platform.

TransFit AI ranks transfer candidates and analyzes how well a player fits a
target club. Transfer Fit V6 separates affordability from sporting quality
and combines verified position, tactical fit, current all-competition output,
three-season evidence, availability, limited age potential, and squad need.

## Current scope

- Target clubs: all 96 official clubs in the Big Five leagues.
- Candidate pool: Premier League, La Liga, Serie A, Bundesliga, and Ligue 1.
- Position investment: user-selected budget in EUR millions with a maximum
  15% stretch allowance.
- Budget checks use Transfermarkt market values from a weekly community
  dataset whenever a reliable player match exists. The TransFit model is a
  clearly labelled fallback for unmatched players.
- Sporting evidence uses Transfermarkt match records across all club
  competitions, with Champions League and stronger domestic leagues weighted
  more heavily. The current season and two previous seasons are included.
- Market value is a transfer benchmark, not an official asking price or a
  completed transfer fee.
- Goalkeepers are not supported yet.
- Transfermarkt profile positions are canonical. Verified lineup positions
  add secondary-role evidence but cannot reclassify a full-back as a winger
  simply because of a formation label.
- Candidate eligibility uses the canonical position. Temporary lineup slots
  can explain tactical versatility but cannot place a natural winger in the
  striker shortlist. Closely related full-back/wing-back and wide-role pairs
  remain grouped where Transfermarkt uses a single canonical label.

## Transfer Fit V6

The final score is a weighted average on a 0-100 scale:

- Current performance: 25%. A 55/45 blend of detailed domestic-league
  percentiles and current all-competition production.
- Tactical fit: 20%.
- Proven level: 20%. Competition-adjusted output and playing time over three
  seasons, with recent seasons weighted more heavily.
- Position and role fit: 15%.
- Availability: 10%, using current all-competition minutes, starts, and
  appearances.
- Potential: 5%. Age is deliberately limited so a young outlier cannot
  dominate the ranking only because of age.
- Squad need: 5%.

For attackers, current total goals and assists carry more weight than per-90
rate. Per-90 output is sample-size regressed and contributes only 25% of the
all-competition production score. Midfielders and defenders use more
position-appropriate playing-time and output blends.

## Architecture

- `api.py`: FastAPI HTTP API.
- `transfit_service.py`: web-facing service layer.
- `candidate_ranking_engine.py`: role-specific candidate ranking.
- `refresh_transfermarkt_values.py`: weekly market-value refresh and player
  identity matching plus source download.
- `build_realistic_player_profiles.py`: verified positions, all-competition
  production, three-season evidence, and availability.
- `realistic_data_engine.py`: shared realism score integration.
- `transfer_fit_v5.py`: Transfer Fit V6 calculation (legacy filename retained
  to avoid breaking existing imports).
- `frontend/`: React and Vite web application.
- `data/raw/`: API-Football exports.
- `data/processed/`: generated position, performance, formation, and tactical
  profiles.

## Data pipeline

Export the configured Big Five leagues:

```powershell
python export_all_leagues.py
```

Build the candidate datasets from the combined export:

```powershell
python build_player_pipeline.py
```

Build formation and tactical profiles for all target clubs:

```powershell
python build_big_five_team_profiles.py
```

The API-Football player pipeline runs these steps:

1. Build a unique Big Five position profile for every player.
2. Merge positions and raw statistics and calculate per-90 metrics.
3. Consolidate players who represented multiple clubs.
4. Rebuild tactical and performance profile inputs.

The combined Big Five export supplies both transfer candidates and target
squad depth. Fixture data supplies formation and tactical profiles for all 96
official target clubs.

### Refresh Transfermarkt evidence

Download the latest community Transfermarkt snapshot, valuations, matches,
appearances, verified lineups, and the Reep provider-ID crosswalk, then
rebuild the local player-value table:

```powershell
python refresh_transfermarkt_values.py --download
```

Build the sporting-evidence table, then refresh tactical profiles so they use
the verified positions:

```powershell
python build_realistic_player_profiles.py
python player_tactical_profiles.py
```

The generated `data/processed/player_market_values_2025.csv` is used by every
ranking and single-player analysis. Matching first uses the API-Football to
Transfermarkt ID crosswalk, guarded against goalkeeper/outfield identity
collisions. A conservative name, club, and age match is used when an ID
mapping is unavailable or incompatible. Review unresolved players in
`data/processed/player_market_values_unmatched_2025.csv`.

The downloaded source files are stored under `data/external/` and are ignored
by Git. The community datasets are free to access, but a future commercial
release should review Transfermarkt's source terms separately.

## Run locally

Create an environment and install the Python dependencies:

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

Start the API:

```powershell
.venv\Scripts\uvicorn api:app --reload
```

Start the frontend in another terminal:

```powershell
cd frontend
npm install
npm run dev
```

The frontend uses `http://127.0.0.1:8000` by default. Set
`VITE_API_BASE_URL` to point it at another API URL.

## API

- `GET /api/health`
- `GET /api/clubs`
- `GET /api/team?team=Arsenal`
- `GET /api/rankings?team=Barcelona&role=ST&budget_millions=50`
- `GET /api/analyze?player=H.%20Kane&player_id=184&team=Barcelona&budget_millions=50`

Passing `player_id` is recommended because the expanded candidate pool can
contain players with similar or duplicate display names.

## Status

Under active development.
