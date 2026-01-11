from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
import pandas as pd

from invest_sim.config.schemas import PortfolioPaths, SimulationConfig


def _max_drawdown(nav: np.ndarray) -> np.ndarray:
    running_max = np.maximum.accumulate(nav, axis=0)
    drawdown = 1.0 - nav / running_max
    return np.max(drawdown, axis=0)


def _time_underwater(nav: np.ndarray) -> np.ndarray:
    running_max = np.maximum.accumulate(nav, axis=0)
    underwater = nav < running_max
    return underwater.mean(axis=0)


def _worst_year_return(nav: np.ndarray, trading_days: int) -> np.ndarray:
    n_years = (nav.shape[0] - 1) // trading_days
    if n_years == 0:
        return np.full(nav.shape[1], np.nan)
    yearly_returns = []
    for year in range(n_years):
        start = year * trading_days
        end = (year + 1) * trading_days
        yearly_returns.append(nav[end] / nav[start] - 1.0)
    return np.min(np.stack(yearly_returns, axis=0), axis=0)


def _expected_shortfall(returns: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    threshold = np.quantile(returns, alpha, axis=0)
    mask = returns <= threshold
    return np.array([
        returns[mask[:, i], i].mean() if mask[:, i].any() else np.nan
        for i in range(returns.shape[1])
    ])


def compute_metrics(
    portfolio_paths: PortfolioPaths,
    sim_config: SimulationConfig,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    nav = portfolio_paths.nav
    daily_returns = nav[1:] / nav[:-1] - 1.0
    final_value = nav[-1]
    years = sim_config.n_years

    # legacy compounded CAGR (includes effect of contributions)
    cagr_legacy = (final_value / nav[0]) ** (1 / years) - 1.0

    # Time-Weighted Return (TWR) neutralisant les apports périodiques
    n_steps = nav.shape[0] - 1
    n_paths = nav.shape[1]
    cashflow = np.zeros((n_steps + 1, n_paths))
    if sim_config.contributions.enabled:
        day_index = min(sim_config.contributions.day_of_month - 1, 20)
        contrib = sim_config.contributions.monthly_amount_eur
        for t in range(n_steps):
            if t % 21 == day_index:
                cashflow[t + 1, :] = contrib

    # rendements périodiques nets des flux : r_t = (nav[t+1] - cashflow[t+1]) / nav[t] - 1
    period_returns = np.zeros((n_steps, n_paths))
    for t in range(n_steps):
        denom = nav[t].copy()
        mask = denom > 0
        period_returns[t, mask] = (
            (nav[t + 1, mask] - cashflow[t + 1, mask]) / denom[mask] - 1.0
        )
        period_returns[t, ~mask] = 0.0

    total_return = np.prod(1.0 + period_returns, axis=0) - 1.0
    cagr = (1.0 + total_return) ** (1.0 / years) - 1.0
    annualized_vol = np.std(daily_returns, axis=0, ddof=1) * np.sqrt(
        sim_config.trading_days_per_year
    )
    max_dd = _max_drawdown(nav)
    time_underwater = _time_underwater(nav)
    worst_year = _worst_year_return(nav, sim_config.trading_days_per_year)
    es_95 = _expected_shortfall(daily_returns, alpha=0.05)

    per_path = pd.DataFrame(
        {
            "final_value": final_value,
            "cagr": cagr,
            "annualized_vol": annualized_vol,
            "max_drawdown": max_dd,
            "time_underwater_fraction": time_underwater,
            "worst_year_return": worst_year,
            "es_95": es_95,
        }
    )

    quantiles = per_path.quantile([0.05, 0.25, 0.75, 0.95])
    quantiles.index = ["p05", "p25", "p75", "p95"]
    summary = pd.concat([per_path.agg(["mean", "median"]), quantiles])
    return per_path, summary


def select_ranking(
    summary_by_strategy: Dict[str, pd.DataFrame],
    max_drawdown_p95_limit: float = 0.70,
) -> pd.DataFrame:
    records = []
    for name, summary in summary_by_strategy.items():
        record = {
            "strategy": name,
            "cagr_p25": summary.loc["p25", "cagr"],
            "cagr_median": summary.loc["median", "cagr"],
            "cagr_p75": summary.loc["p75", "cagr"],
            "cagr_mean": summary.loc["mean", "cagr"],
            "p95_max_drawdown": summary.loc["p95", "max_drawdown"],
            "median_es_95": summary.loc["median", "es_95"],
        }
        records.append(record)
    table = pd.DataFrame(records)
    eligible = table[table["p95_max_drawdown"] <= max_drawdown_p95_limit].copy()
    eligible = eligible.sort_values(
        by=["cagr_median", "median_es_95"], ascending=[False, True]
    )
    eligible["ranking"] = np.arange(1, len(eligible) + 1)
    merged = table.merge(eligible[["strategy", "ranking"]], on="strategy", how="left")
    return merged.sort_values(by=["ranking", "cagr_median"], ascending=[True, False])

def pareto_set(summary_by_strategy: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    records = []
    for name, summary in summary_by_strategy.items():
        records.append(
            {
                "strategy": name,
                "cagr_median": summary.loc["median", "cagr"],
                "p95_max_drawdown": summary.loc["p95", "max_drawdown"],
            }
        )
    table = pd.DataFrame(records)
    pareto = []
    for _, row in table.iterrows():
        dominated = table[
            (table["cagr_median"] >= row["cagr_median"])
            & (table["p95_max_drawdown"] <= row["p95_max_drawdown"])
            & (
                (table["cagr_median"] > row["cagr_median"])
                | (table["p95_max_drawdown"] < row["p95_max_drawdown"])
            )
        ]
        if dominated.empty:
            pareto.append(row)
    return pd.DataFrame(pareto)
