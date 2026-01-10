# PEA Sim (Parametric)
Monte-Carlo simulator for a French PEA-style ETF portfolio using **parametric market models** (no historical time series in the MVP). The project compares strategies (allocation, rebalancing, contributions, leveraged ETFs with daily reset) and produces automated metrics and plots.

## Scope (MVP)
- Daily-step market simulation (252 trading days/year)
- Market models: multivariate GBM, multivariate Student-t, regime switching (calm/crisis)
- Portfolio engine: initial allocation, monthly contributions (approx), rebalancing, transaction costs, TER daily accrual
- Leveraged ETFs: computed from underlying daily returns with daily reset + fees
- Outputs: NAV paths, per-path metrics, summary metrics, plots, ranking + Pareto set

## Install
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .

## Validate configs
pea-sim validate \
  --base configs/base.yaml \
  --universe configs/universe.yaml \
  --cost configs/cost_model.yaml \
  --market configs/market_models/regimes.yaml \
  --strategy configs/strategies/buy_and_hold_world.yaml

## Run a single strategy
pea-sim run \
  --base configs/base.yaml \
  --universe configs/universe.yaml \
  --cost configs/cost_model.yaml \
  --market configs/market_models/regimes.yaml \
  --strategy configs/strategies/buy_and_hold_world.yaml

## Compare all strategies in a directory
pea-sim compare \
  --base configs/base.yaml \
  --universe configs/universe.yaml \
  --cost configs/cost_model.yaml \
  --market configs/market_models/regimes.yaml \
  --strategies-dir configs/strategies/

## Outputs
Each run creates a folder under runs/:

config_snapshot/ (YAMLs used)
nav_paths.npy (optional)
metrics_per_path.csv, metrics_summary.csv
plots/ (fan chart, CDFs, scatter)
report.md (summary + ranking)

## Notes / limitations
This MVP is an analysis-of-scenarios framework: results depend on the chosen parameters (drift, vol, correlations, regime behavior). It is not a historical backtest. A later phase can add data ingestion and calibration on real time series without changing the core interfaces.
