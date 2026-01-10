# PEA Sim Parametric

Parametric Monte-Carlo simulation of a French PEA-style portfolio. The simulator uses **model-based** daily returns (GBM, Student-t, or regime-switching) without any external market data or historical calibration. It supports static allocations, rebalancing, contributions, and leveraged ETFs with daily reset, and produces reproducible output runs with plots and metrics.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Quick start

Validate configs:

```bash
pea-sim validate \
  --base configs/base.yaml \
  --universe configs/universe.yaml \
  --cost configs/cost_model.yaml \
  --market configs/market_models/regimes.yaml \
  --strategy configs/strategies/buy_and_hold_world.yaml
```

Run a single strategy:

```bash
pea-sim run \
  --base configs/base.yaml \
  --universe configs/universe.yaml \
  --cost configs/cost_model.yaml \
  --market configs/market_models/regimes.yaml \
  --strategy configs/strategies/buy_and_hold_world.yaml
```

Compare all strategies:

```bash
pea-sim compare \
  --base configs/base.yaml \
  --universe configs/universe.yaml \
  --cost configs/cost_model.yaml \
  --market configs/market_models/regimes.yaml \
  --strategies-dir configs/strategies
```

## Notes and assumptions

- All models are parametric: **no historical data** is loaded or calibrated in this project.
- Daily time steps are used internally, especially when leverage is present.
- Leveraged assets are computed from underlying base returns using a daily reset:
  `r_L = leverage * r_underlying - fee_daily`.
- Volatility targeting never synthetically borrows. If the strategy does not already contain leveraged assets, any requested leverage above 1.0 is capped at 1.0.

## Output

Each run writes a timestamped folder in `runs/` with:

- `config_snapshot/` YAML copies
- `nav_paths.npy`
- `metrics_per_path.csv`
- `metrics_summary.csv`
- `plots/*.png`
- `report.md`

