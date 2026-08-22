# TransFit AI

[![CI](https://github.com/Samhij106/TransFit-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/Samhij106/TransFit-AI/actions/workflows/ci.yml)
[![Live Demo](https://img.shields.io/badge/live_demo-open_transfit-9CFF2E?style=flat-square&labelColor=07100A)](https://transfit-ai-samhij106.onrender.com)

[**Open the live demo**](https://transfit-ai-samhij106.onrender.com) ·
[Model card](docs/ML_MODEL_CARD.md) ·
[Data-quality report](docs/DATA_QUALITY_REPORT.md) ·
[API health](https://transfit-ai-samhij106-api.onrender.com/api/health)

![TransFit AI — Player plus club, one score](frontend/public/og-transfit.png)

AI-powered football transfer fit analysis platform.

TransFit AI ranks transfer candidates and analyzes how well a player fits a
target club. TransFit V12 is a genuine hybrid and explainable AI system: a transparent
football expert engine is combined with two supervised models trained on
12,317 historical transfers. The first forecasts first-season transfer
success; the second uses pairwise learning-to-rank to compare candidates for
the same club and positional family. The UI exposes every component instead
of hiding the recommendation behind one unexplained score. A shared XAI layer
traces the recommendation back to every engine, weighted factor, confidence
signal, guardrail, and non-causal model driver.

The product has four complementary workflows:

1. Analyze a specific player: club and formation selection, verified player
   search, optional deal budget, and a player-to-club TransFit Score.
2. Find transfer candidates: club, one of its two most-used formations,
   natural position, and investment budget, followed by a ranked shortlist.
3. Compare players: select a target club, formation and two to four players,
   then compare
   their club-specific TransFit scores, weighted dimensions, market values,
   and the decisive reasons behind the winner.
4. Plan a transfer window: select a club, one of its two most-used verified
   formations and a total budget. The user can request between one and eight
   transfers or leave the count on Auto so the model selects the strongest
   meaningful upgrade plan. Safe, Balanced, and Ambitious plans are optimized.

> **Public-demo note:** the free API may sleep after inactivity. The first
> analysis can therefore take about 30–60 seconds while Render wakes it up;
> later requests are normally much faster.

## Recommended demo paths

These short flows make the model's behaviour easy to present:

1. **Explain one decision:** choose a club and formation, analyze a specific
   player, then open the evidence and AI explanation. The report separates
   football fit, historical-ML prediction, pairwise rank evidence, confidence,
   risks, and any realism cap.
2. **Test a realistic shortlist:** choose a smaller club, select its natural
   positional need, and enter a large budget. The engine still applies club
   stature and sporting-step ceilings instead of recommending an unrealistic
   superstar simply because the money is available.
3. **Build a complete window:** choose one of the club's two verified
   formations, set a total budget, and leave the transfer count on Auto. Compare
   the Safe, Balanced, and Ambitious plans and the projected XI.

## Technology stack

| Layer | Technology |
| --- | --- |
| Product UI | React 19, Vite 8, responsive custom CSS |
| API | FastAPI, Uvicorn, typed JSON endpoints |
| ML and data | scikit-learn, pandas, NumPy, joblib, DuckDB training pipeline |
| Explainability | weighted expert trace, historical-model drivers, confidence and guardrails |
| Deployment | Render Blueprint: static frontend plus Python web service |
| Quality | Python unittest suite, football realism benchmarks, Oxlint, GitHub Actions |

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
- Candidate eligibility also checks the target club's squad-value tier,
  realistic signing ceiling, the player's current club tier, and the size of
  the sporting-status step. Clearly unrealistic moves are removed from
  shortlists even when the user enters a very large budget.
- Goalkeepers are not supported yet.
- Transfermarkt profile positions are canonical. Verified lineup positions
  add secondary-role evidence but cannot reclassify a full-back as a winger
  simply because of a formation label.
- Candidate eligibility uses the canonical position. Temporary lineup slots
  can explain tactical versatility but cannot place a natural winger in the
  striker shortlist. Closely related full-back/wing-back and wide-role pairs
  remain grouped where Transfermarkt uses a single canonical label.

## TransFit V12 Explainable AI

The final score is calculated as:

```text
TransFit Score = 70% expert-engine score
                 + 28.5% historical success percentile
                 + 1.5% pairwise club-role rank score
```

The success model estimates the quality of the first 365 days after a player
joins a target club. It was trained on transfers from 2014–2025 with a chronological
train/validation/test split, using 24 pre-transfer player, club, league and
market features. On 1,222 unseen recent transfers it achieved MAE 17.62 versus
22.50 for the median baseline, NDCG@10 0.850 versus 0.716, and success AUC
0.719 versus 0.500. Separate quantile models provide a visible 10–90%
prediction interval.

The second model is a genuine pairwise learning-to-rank classifier. Its
training examples compare two transfers made by the same destination club in
the same season and broad positional family. It learned from 33,982
development comparisons and was tested on 3,990 later, unseen comparisons.
Pairwise held-out AUC is 0.793 and accuracy is 0.722. On the role-conditioned
test groups, the conservative 95% success-model / 5% ranker ML blend achieved
NDCG@10 0.9212 versus 0.9207 for the success model alone.

The standalone ranker was less stable than the pointwise success model, so it
is intentionally limited to 5% of the historical-ML block, or 1.5% of the
final TransFit Score. This is enough to break close ties using club-role
evidence without allowing a sparse club pattern to overrule football quality.
For predictable public-demo latency, all-vs-all inference runs on the strongest
80 candidates that already passed the realism and budget filters.

### Explainability layer

Every isolated player analysis, comparison report and live candidate ranking
includes a machine-readable `explainability` object produced in the Backend.
It contains:

- a complete expert / historical-ML / club-role-ranker decision trace;
- the score and weighted points contributed by every available engine;
- the strongest weighted football factors and the main risks to verify;
- model-agnostic one-feature counterfactual drivers for the historical model;
- an evidence-confidence score based on data coverage and interval certainty;
- explicit realism caps, calibration adjustments and model limitations.

These explanations describe model behaviour and decision evidence. They are
not causal claims and do not represent the probability that a transfer occurs.

### Data-quality and outlier controls

Performance percentages are sample-aware: shot accuracy and dribble success
are shrunk toward the relevant position-group average when they are based on a
small number of attempts. UI bars show position percentiles while preserving
the raw statistic and its unit. Run `audit_player_analysis_data.py` to check
hard ranges, broken statistical relationships, missing values, low-sample rate
risks and robust outlier review candidates. The current audit is documented in
[`docs/DATA_QUALITY_REPORT.md`](docs/DATA_QUALITY_REPORT.md).

The model output is a forecast of post-transfer sporting success—not the
probability that negotiations will be completed. If the player or club cannot
be matched reliably, the application explicitly falls back to the expert
engine and does not invent an ML result. See the complete
[ML model card](docs/ML_MODEL_CARD.md).

### Expert engine

The expert component is a weighted average on a 0-100 scale:

- Current performance: 27%. Detailed domestic-league percentiles are blended
  with all-competition output using role-specific weights. Goals and assists
  matter most for attackers and minimally for deeper positions.
- Tactical fit: 22.5%.
- Proven level: 13.5%. Current role quality, competition-adjusted three-season
  evidence, and a modest Transfermarkt percentile among positional peers.
- Position and role fit: 13.5%.
- Availability: 4.5%, using current all-competition minutes, starts, and
  appearances.
- Potential: 4.5%. Age is deliberately limited so a young outlier cannot
  dominate the ranking only because of age.
- Squad need: 4.5%.
- Deal feasibility: 10%. Club stature, squad value, realistic recruitment
  ceiling, current-club status and player level define whether the path is
  realistic, ambitious or unrealistic. An unrealistic result is capped and
  excluded from automatic candidate lists.

For attackers, current total goals and assists carry more weight than per-90
rate. Deeper roles are driven primarily by their role-specific metrics such as
passing, ball winning, creation, and tactical compatibility. Market validation
is an external guardrail inside Proven Level; market value still controls
affordability separately and is not treated as an asking price.

## Architecture

- `api.py`: FastAPI HTTP API.
- `transfit_service.py`: web-facing service layer.
- `ml/build_transfer_dataset.py`: leakage-safe historical label and feature
  pipeline built from the Transfermarkt community DuckDB dataset.
- `ml/train_transfer_success.py`: chronological validation, hyperparameter
  selection, gradient-boosting and quantile-model training, evaluation and
  artifact export.
- `ml/build_inference_context.py`: compact current player, club and alias
  tables for production inference.
- `ml/transfer_success_engine.py`: production feature construction, batch
  prediction, uncertainty, percentile calibration and safe fallback.
- `ml/train_transfer_ranker.py`: leakage-safe pair generation, pairwise
  classifier training, chronological evaluation and blend comparison.
- `ml/transfer_ranker_engine.py`: live all-vs-all candidate comparison and
  club-role rank score inference.
- `models/transfer_success_v1.joblib`: tracked trained model artifact.
- `models/transfer_success_v1_metadata.json`: dataset hash, split, metrics,
  calibration and feature importance.
- `models/transfer_ranker_v1.joblib`: tracked pairwise ranker artifact.
- `models/transfer_ranker_v1_metadata.json`: pair counts, held-out ranking
  metrics, baseline comparison and the conservative blend policy.
- `explainability_engine.py`: shared V12 decision trace, factor attribution,
  evidence confidence, ML-driver translation and disclosure layer.
- `candidate_ranking_engine.py`: role-specific candidate ranking.
- `squad_planner_service.py`: squad audit and budget-constrained transfer
  window optimizer built on the same V12 explainable dual-ML scores.
- `transfer_realism_engine.py`: data-driven club-stature profiles, recruitment
  ceilings, transfer-path scoring and hard realism exclusions.
- `refresh_transfermarkt_values.py`: weekly market-value refresh and player
  identity matching plus source download.
- `build_realistic_player_profiles.py`: verified positions, all-competition
  production, three-season evidence, and availability.
- `realistic_data_engine.py`: shared realism score integration.
- `transfer_fit_v5.py`: expert-engine calculation (legacy filename retained
  to avoid breaking existing imports).
- `validate_model_benchmarks.py`: football sanity-check suite that protects
  known realistic ordering and canonical-position exclusions.
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

### Rebuild the historical ML model

Install the training-only dependency and place the community DuckDB snapshot
at `data/external/transfermarkt-datasets.duckdb`, then run:

```powershell
.venv\Scripts\pip install -r requirements-ml.txt
.venv\Scripts\python.exe -m ml.build_transfer_dataset
.venv\Scripts\python.exe -m ml.train_transfer_success
.venv\Scripts\python.exe -m ml.build_inference_context
```

The first command builds labels strictly from the 365 days after each
transfer, while all 24 input features come from information available before
the transfer. The trainer uses chronological splits and writes held-out
metrics plus a SHA-256 dataset fingerprint. The 211 MB source database and
generated training table remain outside Git; the small production context,
model and metadata are tracked.

## Run locally

Create an environment and install the Python dependencies:

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

The checked-in data and model artifacts are sufficient for the application.
Only copy `.env.example` to `.env` and add `API_FOOTBALL_KEY` when refreshing
API-Football source data:

```powershell
Copy-Item .env.example .env
```

Start the API:

```powershell
.venv\Scripts\uvicorn api:app --reload
```

Start the frontend in another terminal:

```powershell
cd frontend
npm ci
npm run dev
```

The frontend uses `http://127.0.0.1:8000` by default. Set
`VITE_API_BASE_URL` to point it at another API URL; `frontend/.env.example`
contains the local default.

## Free public demo

**Live application:** <https://transfit-ai-samhij106.onrender.com>

**Live API health check:**
<https://transfit-ai-samhij106-api.onrender.com/api/health>

The repository includes `render.yaml`, which creates two free Render services:

- `transfit-ai-samhij106`: the React static site.
- `transfit-ai-samhij106-api`: the FastAPI analysis service.

Create a new Render Blueprint from this repository to deploy both services.
The public frontend is configured to call the deployed API, and the API accepts
requests from the deployed frontend through `FRONTEND_ORIGINS`. Localhost
origins remain enabled for development.

Free Render web services sleep after inactivity. The frontend shows a delayed
engine-starting notice so portfolio visitors understand the first request can
take longer without interrupting normal fast requests.

## Model benchmarks

Run the regression tests and the football benchmark suite before accepting a
scoring-model change:

```powershell
.venv\Scripts\python.exe -m unittest test_transfit_v7.py
.venv\Scripts\python.exe -m unittest test_squad_planner.py
.venv\Scripts\python.exe -m unittest test_ml_transfer_success.py
.venv\Scripts\python.exe validate_model_benchmarks.py
```

The benchmark definitions live in
`data/benchmarks/transfit_v7_benchmarks.json`. They currently protect the
Barcelona CDM ordering that keeps Rodri above Casemiro, realistic striker
quality ordering, and the exclusion of natural left wingers from the ST
shortlist. Add a case whenever a confirmed football outlier is found and
fixed.

### Continuous integration

Every push to `main` and every pull request runs two independent GitHub Actions
jobs:

- Backend dependency validation, the complete Python test suite, and the
  football realism benchmark suite.
- Frontend dependency installation, Oxlint checks, and a Vite production build.

Dependabot also checks Python, npm, and GitHub Actions dependencies weekly.
See the live [CI workflow](https://github.com/Samhij106/TransFit-AI/actions/workflows/ci.yml).

## API

- `GET /api/health`
- `GET /api/ml/model` (model version and held-out metrics)
- `GET /api/clubs`
- `GET /api/players?q=joao&team=AC%20Milan&limit=12`
- `GET /api/team?team=Arsenal`
- `GET /api/rankings?team=Barcelona&role=ST&formation=4-3-3&budget_millions=50`
- `GET /api/analyze?player=H.%20Kane&player_id=184&team=Barcelona&formation=4-3-3&budget_millions=50`
- `GET /api/compare?team=Barcelona&player_ids=184,217,6009&formation=4-3-3&budget_millions=120`
- `GET /api/squad-plan?team=Barcelona&budget_millions=150&max_signings=5&formation=4-3-3`
- `GET /api/squad-plan?team=Barcelona&budget_millions=150&formation=4-3-3` (Auto transfer count)

Passing `player_id` is recommended because the expanded candidate pool can
contain players with similar or duplicate display names.

The squad-plan endpoint treats the selected amount as a total transfer-fee
budget. Safe and Balanced plans stay within that amount; Ambitious may use the
same 15% tolerance as the candidate workflow. Wages, contract terms, and a
selling club's willingness to negotiate are deliberately outside the current
model boundary. The formation must be one of the club's two most-used
supported shapes returned by `GET /api/team` in `formation_options`. When
fewer than two shapes are present in the verified
match data, only the real available options are returned.

## Status

Portfolio-ready public research demo under active development. The current
model boundary is explicit: goalkeepers, wages, contract terms, agent
preferences, and the selling club's willingness to negotiate are not yet
modelled. See [SECURITY.md](SECURITY.md) for responsible disclosure and secret
handling.
