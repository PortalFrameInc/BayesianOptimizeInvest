from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd

from pea_sim.config import load_cost_model, load_market_model, load_simulation, load_strategy, load_universe
from pea_sim.config.schemas import MarketModelConfig, PortfolioPaths
from pea_sim.market.gbm import GBMModel
from pea_sim.market.regimes import RegimeSwitchingModel
from pea_sim.market.student_t import StudentTModel
from pea_sim.metrics import compute_metrics, pareto_set, select_ranking
from pea_sim.portfolio import simulate_portfolio
from pea_sim.reporting import (
    plot_cdf,
    plot_nav_fanchart,
    plot_scatter_cagr_vs_dd,
    write_report,
)


@dataclass
class RunResult:
    output_dir: Path
    portfolio_paths: PortfolioPaths
    metrics_per_path: pd.DataFrame
    metrics_summary: pd.DataFrame


def _market_model_from_config(config: MarketModelConfig):
    if config.model_type == "gbm":
        return GBMModel()
    if config.model_type == "student_t":
        return StudentTModel()
    if config.model_type == "regimes":
        return RegimeSwitchingModel()
    raise ValueError(f"Unknown model type {config.model_type}")


def _snapshot_configs(output_dir: Path, config_paths: List[Path]) -> None:
    snapshot_dir = output_dir / "config_snapshot"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    for path in config_paths:
        snapshot_dir.joinpath(path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def run_experiment(
    base_path: Path,
    universe_path: Path,
    cost_path: Path,
    market_path: Path,
    strategy_path: Path,
) -> RunResult:
    sim_config = load_simulation(base_path)
    universe = load_universe(universe_path)
    cost_model = load_cost_model(cost_path)
    market_config = load_market_model(market_path)
    strategy = load_strategy(strategy_path)

    model = _market_model_from_config(market_config)
    fitted = model.fit(universe, market_config, sim_config)
    market_paths = model.sample_paths(fitted, sim_config)
    portfolio_paths = simulate_portfolio(market_paths, universe, strategy, cost_model, sim_config)

    metrics_per_path, metrics_summary = compute_metrics(portfolio_paths, sim_config)

    output_dir = Path(sim_config.output.base_dir) / f"{pd.Timestamp.utcnow():%Y%m%d_%H%M%S}_{sim_config.run_name}"
    output_dir.mkdir(parents=True, exist_ok=True)

    _snapshot_configs(output_dir, [base_path, universe_path, cost_path, market_path, strategy_path])

    if sim_config.output.save_nav_paths:
        np.save(output_dir / "nav_paths.npy", portfolio_paths.nav)
    if sim_config.output.save_weights_paths and portfolio_paths.weights is not None:
        np.save(output_dir / "weights_paths.npy", portfolio_paths.weights)
    if sim_config.output.save_turnover_paths and portfolio_paths.turnover is not None:
        np.save(output_dir / "turnover_paths.npy", portfolio_paths.turnover)

    metrics_per_path.to_csv(output_dir / "metrics_per_path.csv", index=False)
    metrics_summary.to_csv(output_dir / "metrics_summary.csv")

    plots_dir = output_dir / "plots"
    plots_dir.mkdir(exist_ok=True)
    plot_nav_fanchart(portfolio_paths.nav, plots_dir / "nav_fanchart.png")
    plot_cdf(
        metrics_per_path["final_value"].values,
        "Final value CDF",
        "Final value (EUR)",
        plots_dir / "final_value_cdf.png",
    )
    plot_cdf(
        metrics_per_path["max_drawdown"].values,
        "Max drawdown CDF",
        "Max drawdown",
        plots_dir / "max_drawdown_cdf.png",
    )
    plot_scatter_cagr_vs_dd(
        pd.DataFrame(
            {
                "strategy": [strategy.name],
                "median_cagr": [metrics_summary.loc["median", "cagr"]],
                "p95_max_drawdown": [metrics_summary.loc["p95", "max_drawdown"]],
            }
        ),
        plots_dir / "scatter_cagr_vs_dd95.png",
    )

    ranking = select_ranking({strategy.name: metrics_summary})
    pareto = pareto_set({strategy.name: metrics_summary})
    write_report(
        output_dir,
        [base_path, universe_path, cost_path, market_path, strategy_path],
        metrics_summary,
        ranking,
        pareto,
    )

    return RunResult(
        output_dir=output_dir,
        portfolio_paths=portfolio_paths,
        metrics_per_path=metrics_per_path,
        metrics_summary=metrics_summary,
    )
