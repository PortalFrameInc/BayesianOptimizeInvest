from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import pandas as pd

from invest_sim.config import load_cost_model, load_market_model, load_simulation, load_strategy, load_universe
from invest_sim.market.gbm import GBMModel
from invest_sim.market.regimes import RegimeSwitchingModel
from invest_sim.market.student_t import StudentTModel
from invest_sim.metrics import compute_metrics, pareto_set, select_ranking
from invest_sim.portfolio import simulate_portfolio
from invest_sim.reporting import plot_strategy_cdf, plot_strategy_scatter, write_comparison_report


@dataclass
class ComparisonResult:
    output_dir: Path
    metrics_summary: pd.DataFrame


def _market_model_from_config(model_type: str):
    if model_type == "gbm":
        return GBMModel()
    if model_type == "student_t":
        return StudentTModel()
    if model_type == "regimes":
        return RegimeSwitchingModel()
    raise ValueError(f"Unknown model type {model_type}")


def compare_strategies(
    base_path: Path,
    universe_path: Path,
    cost_path: Path,
    market_path: Path,
    strategies_dir: Path,
) -> ComparisonResult:
    sim_config = load_simulation(base_path)
    universe = load_universe(universe_path)
    cost_model = load_cost_model(cost_path)
    market_config = load_market_model(market_path)

    model = _market_model_from_config(market_config.model_type)
    fitted = model.fit(universe, market_config, sim_config)
    market_paths = model.sample_paths(fitted, sim_config)

    metrics_by_strategy: Dict[str, pd.DataFrame] = {}
    summary_by_strategy: Dict[str, pd.DataFrame] = {}

    # recursively find .yaml and .yml files in the strategies directory
    strategy_files = sorted(
        [p for ext in ("*.yaml", "*.yml") for p in strategies_dir.rglob(ext)]
    )
    if not strategy_files:
        raise ValueError(f"No strategy files found under {strategies_dir}")
    for strategy_path in strategy_files:
        strategy = load_strategy(strategy_path)
        portfolio_paths = simulate_portfolio(market_paths, universe, strategy, cost_model, sim_config)
        per_path, summary = compute_metrics(portfolio_paths, sim_config)
        metrics_by_strategy[strategy.name] = per_path
        summary_by_strategy[strategy.name] = summary

    summary_rows = []
    for name, summary in summary_by_strategy.items():
        row = {"strategy": name}
        for stat in summary.index:
            for metric in summary.columns:
                row[f"{metric}_{stat}"] = summary.loc[stat, metric]
        summary_rows.append(row)
    summary_table = pd.DataFrame(summary_rows)

    output_dir = Path(sim_config.output.base_dir) / f"{pd.Timestamp.utcnow():%Y%m%d_%H%M%S}_compare_{sim_config.run_name}"
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_table.to_csv(output_dir / "metrics_summary_all_strategies.csv", index=False)

    plots_dir = output_dir / "plots"
    plots_dir.mkdir(exist_ok=True)
    plot_strategy_scatter(
        pd.DataFrame(
            {
                "strategy": list(summary_by_strategy.keys()),
                "median_cagr": [summary.loc["median", "cagr"] for summary in summary_by_strategy.values()],
                "p95_max_drawdown": [summary.loc["p95", "max_drawdown"] for summary in summary_by_strategy.values()],
            }
        ),
        plots_dir / "scatter_cagr_vs_dd95.png",
    )
    plot_strategy_cdf(metrics_by_strategy, "final_value", plots_dir / "final_value_cdf.png")
    plot_strategy_cdf(metrics_by_strategy, "max_drawdown", plots_dir / "max_drawdown_cdf.png")

    ranking = select_ranking(summary_by_strategy)
    pareto = pareto_set(summary_by_strategy)
    write_comparison_report(output_dir, summary_table, ranking, pareto, sim_config.model_dump())

    return ComparisonResult(output_dir=output_dir, metrics_summary=summary_table)
