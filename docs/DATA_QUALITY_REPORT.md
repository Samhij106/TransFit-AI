# Player Analysis Data Quality Report

Audit date: 2026-08-22  
Dataset: `data/processed/player_profiles_season_2025.csv`  
Rows audited: 2,097

## Result

- Hard numerical range errors: **0**
- Broken relationships (for example shots on target greater than shots): **0**
- Missing values in audited fields: **9**
  - one missing age (`K. Tunde`)
  - eight missing pass-accuracy values
- Model-relevant low-sample percentage risks: **71**
  - 18 shot-accuracy records for forwards
  - 53 dribble-success records for fullbacks or wide players

The low-sample records are not necessarily incorrect. They become misleading
when a percentage based on one to six actions is treated like a stable season
rate. Examples include fullbacks with 100% dribble success from one or two
attempts.

## Safeguards added

1. Shot accuracy and dribble success are now empirically shrunk toward the
   player's position-group average using a 12-attempt prior.
2. The raw value remains visible, but ranking uses the sample-adjusted value.
3. Every performance bar is based on a position-specific percentile instead of
   mixing incompatible raw units such as percentages, totals and per-90 rates.
4. Missing age now produces a neutral development-runway estimate and a `null`
   age in the API instead of allowing `NaN` to propagate.
5. Per-90 statistical extremes are flagged for review, not automatically
   deleted. Legitimately elite players such as Harry Kane and Lamine Yamal can
   be true statistical outliers.

## Reproduce the audit

```powershell
.\.venv\Scripts\python.exe audit_player_analysis_data.py
```

To save a machine-readable report:

```powershell
.\.venv\Scripts\python.exe audit_player_analysis_data.py --output data/quality/player_analysis_audit.json
```

Robust outlier candidates are review signals rather than proof of corrupted
data. A football model should preserve genuine exceptional performance while
controlling for sample size and invalid records.
