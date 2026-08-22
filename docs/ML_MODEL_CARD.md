# TransFit historical ML model card

## Model summary

- Model ID: `transfer-success-hgb-v1`
- Ranker ID: `transfer-ranker-pairwise-hgb-v1`
- Product layer: `TransFit V11 Dual-ML Ranking`
- Algorithm: scikit-learn histogram gradient-boosting regressor
- Purpose: estimate the quality of a player's first 365 days after a transfer
  to a specific club, using only information available before the transfer.
- Final candidate score: 70% expert-system score, 28.5% historical-prediction
  percentile and 1.5% pairwise club-role rank score. Raw model outputs are
  shown separately.

This is a supervised machine-learning model. It is not a language model, a
transfer-rumour generator, or a probability that a deal will happen.

The product contains two supervised models: a pointwise outcome regressor and
a pairwise learning-to-rank classifier. Single-player analysis uses the
pointwise model because a pairwise score only exists inside a candidate pool.

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

## Pairwise learning-to-rank model

The ranker creates a pair only when both historical transfers share the same
destination club, transfer season and broad position. Pairs whose outcome
difference is smaller than eight points are removed as noisy near-ties. Both
directions are included, and the training weight grows with the observed
outcome gap.

- Development comparisons: 33,982
- Held-out comparisons: 3,990
- Held-out pairwise AUC: 0.793
- Held-out pairwise accuracy: 0.722
- Standalone ranker NDCG@10: 0.913
- Pointwise success-model NDCG@10 on the same groups: 0.921
- Conservative 95/5 ML blend NDCG@10: 0.9212

The standalone ranker did not beat the pointwise model, so it was not given a
large product weight. The fixed 5% contribution inside the ML block produced
a small held-out ranking lift while limiting temporal instability. This means
the ranker can break close candidate ties but cannot make a weak player outrank
an elite player by itself.

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
- a relative club-role rank score, calculated through all-vs-all pairwise
  comparisons inside the filtered live candidate pool

For production latency, pairwise comparison is limited to the strongest 80
eligible candidates after the realism and budget filters. Candidates outside
that preselection keep the pointwise success-model fallback score; normal API
and squad planner limits are smaller than this pool.

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
- Pairwise club-role groups are sparse for some clubs. The ranker is therefore
  a conservative secondary signal rather than the dominant recommendation.
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
.venv\Scripts\python.exe -m ml.train_transfer_ranker
.venv\Scripts\python.exe -m ml.build_inference_context
```

The trainer writes a dataset hash, split dates, selected hyperparameters,
calibration table, permutation importance and test metrics to
`models/transfer_success_v1_metadata.json`.

The ranker trainer writes its split, comparison counts, pairwise metrics,
pointwise baseline and blend policy to
`models/transfer_ranker_v1_metadata.json`.

## Intended use

TransFit is portfolio-grade decision support for exploring football
recruitment logic. It should be used to generate and compare hypotheses, not to
make autonomous financial or employment decisions.
