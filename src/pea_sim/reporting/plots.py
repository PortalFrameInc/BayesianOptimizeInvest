from __future__ import annotations

from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pea_sim.config.schemas import PortfolioPaths


def plot_nav_fanchart(nav: np.ndarray, output_path: Path) -> None:
    quantiles = np.quantile(nav, [0.05, 0.25, 0.5, 0.75, 0.95], axis=1)
    x = np.arange(nav.shape[0])
    plt.figure(figsize=(8, 4))
    plt.fill_between(x, quantiles[0], quantiles[4], color="skyblue", alpha=0.3, label="5-95%")
    plt.fill_between(x, quantiles[1], quantiles[3], color="steelblue", alpha=0.4, label="25-75%")
    plt.plot(x, quantiles[2], color="navy", label="Median")
    plt.xlabel("Day")
    plt.ylabel("NAV")
    plt.title("NAV fan chart")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def plot_cdf(series: np.ndarray, title: str, xlabel: str, output_path: Path) -> None:
    sorted_vals = np.sort(series)
    y = np.linspace(0, 1, len(sorted_vals))
    plt.figure(figsize=(6, 4))
    plt.plot(sorted_vals, y)
    plt.xlabel(xlabel)
    plt.ylabel("CDF")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def plot_scatter_cagr_vs_dd(summary: pd.DataFrame, output_path: Path) -> None:
    plt.figure(figsize=(6, 4))
    plt.scatter(summary["median_cagr"], summary["p95_max_drawdown"], color="tab:blue")
    for _, row in summary.iterrows():
        plt.annotate(row["strategy"], (row["median_cagr"], row["p95_max_drawdown"]), fontsize=8)
    plt.xlabel("Median CAGR")
    plt.ylabel("P95 Max Drawdown")
    plt.title("CAGR vs Drawdown (P95)")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def plot_strategy_cdf(metrics_by_strategy: Dict[str, pd.DataFrame], column: str, output_path: Path) -> None:
    plt.figure(figsize=(6, 4))
    for name, metrics in metrics_by_strategy.items():
        data = np.sort(metrics[column].values)
        y = np.linspace(0, 1, len(data))
        plt.plot(data, y, label=name)
    plt.xlabel(column)
    plt.ylabel("CDF")
    plt.title(f"{column} CDF")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def plot_strategy_scatter(summary: pd.DataFrame, output_path: Path) -> None:
    plot_scatter_cagr_vs_dd(summary, output_path)
