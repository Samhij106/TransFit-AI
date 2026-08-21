# TransFit historical transfer-success model card

## Model summary

- Model ID: `transfer-success-hgb-v1`
- Product layer: `TransFit V10 Historical ML Hybrid`
- Algorithm: scikit-learn histogram gradient-boosting regressor
- Purpose: estimate the quality of a player's first 365 days after a transfer
  to a specific club, using only information available before the transfer.
- Final product score: 70% expert-system score and 30% historical-prediction
  percentile. The raw ML forecast is shown separately.

This is a supervised machine-learning model. It is not a language model, a
transfer-rumour generator, or a probability that a deal will happen.

## Data

The training table is generated from the public community Transfermarkt
dataset stored locally as DuckDB. The source database itself is ignored by Git;
the trained artifact, inference context, metadata and reproducible pipeline are
tracked.

- Labeled transfers: 12,317
- Unique players: 4,353
- Destination clubs: 167
- Transfer dates: 2014-07-01 through 2025-06-10
- Destination competitions: Premier League, La Liga, Serie A, Bundesliga and
  Ligue 1
- Goalkeepers: excluded from V1

Only pre-transfer features are used. Outcomes that happen after the transfer
are used exclusively to build the label.

## Target definition

For every qualifying transfer, the model measures the following 365 days:

- 50% destination-club minutes share
- 25% destination-club starting-lineup share
- 10% appearance share
- 10% market-value outcome relative to the pre-transfer value
- 5% evidence that the player remained active late in the evaluation window

The result is clipped to a 0–100 `success_score`. A score of 60 or above is
used only for the reported classification AUC; training is regression on the
continuous target.

## Features

The model has 24 features:

- Player state: age, market value, 180-day value trend, prior appearances,
  starts, minutes, goals, assists, goal contributions per 90, minutes share,
  starts share and transfers during the previous three years.
- Club context: source and target points per game, source and target goal
  difference per game, league-strength gap, cross-border flag and transfer
  window.
- Categorical context: broad position, sub-position, source competition,
  destination competition and destination club.

No post-transfer feature is available to the model at inference time.

## Validation design

The split is chronological to avoid learning from the future:

- Train: transfers through 2023-06-30 — 9,406 rows
- Validation: 2023-07-01 through 2024-06-30 — 1,689 rows
- Held-out test: after 2024-06-30 — 1,222 rows

Hyperparameters are selected on validation MAE, with NDCG@10 as a secondary
ranking criterion. The held-out test set is evaluated once after selection.

## Held-out results

| Metric | Model | Median baseline |
| --- | ---: | ---: |
| MAE | 17.623 | 22.502 |
| RMSE | 23.101 | 28.979 |
| R² | 0.172 | -0.304 |
| NDCG@10 | 0.850 | 0.716 |
| Success AUC | 0.719 | 0.500 |

The separate 10th- and 90th-quantile models produced 75.3% empirical interval
coverage on the held-out test set. The interval is displayed in the product so
uncertain recommendations are not presented as precise facts.

## Inference and fallback

Current players are matched to Transfermarkt identities, while current target
clubs are resolved through a compact alias table. The application constructs
the same 24 features and returns:

- raw success forecast
- historical prediction percentile
- 10–90% prediction interval
- low, medium or high confidence based on interval width
- local positive and negative model signals, calculated by replacing one
  feature at a time with the development-set median or mode

The local signals are model-agnostic counterfactual sensitivity checks. They
are deliberately marked as non-causal and are not additive SHAP values.

If a reliable player or club identity match is unavailable, the application
does not invent a value. It returns no ML prediction and safely uses the expert
engine alone.

## Known limitations

- Observational football data contains selection bias: clubs choose which
  players to sign, and the model does not observe every rejected alternative.
- Wages, contract length, injury details, coach changes, language, personality,
  agent influence and selling-club willingness are not modeled.
- Market value is an imperfect proxy and is not an asking price.
- Historical club IDs can encode club-specific patterns that may drift over
  time.
- The V1 label rewards early minutes and starts, so a good long-term transfer
  with a slow first season can be underrated.
- The model supports outfield players only.
- Prediction intervals describe model uncertainty under historical patterns;
  they do not cover every real-world shock.

## Reproducibility

With the source DuckDB file available at
`data/external/transfermarkt-datasets.duckdb`:

```powershell
.venv\Scripts\python.exe -m ml.build_transfer_dataset
.venv\Scripts\python.exe -m ml.train_transfer_success
.venv\Scripts\python.exe -m ml.build_inference_context
```

The trainer writes a dataset hash, split dates, selected hyperparameters,
calibration table, permutation importance and test metrics to
`models/transfer_success_v1_metadata.json`.

## Intended use

TransFit is portfolio-grade decision support for exploring football
recruitment logic. It should be used to generate and compare hypotheses, not to
make autonomous financial or employment decisions.
