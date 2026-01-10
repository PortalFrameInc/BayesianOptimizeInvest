from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd


def write_report(
    output_dir: Path,
    config_files: List[Path],
    summary: pd.DataFrame,
    ranking: pd.DataFrame,
    pareto: pd.DataFrame,
) -> None:
    lines = ["# PEA Simulation Report", "", "## Configs", ""]
    for cfg in config_files:
        lines.append(f"- {cfg.name}")
    lines.append("")
    lines.append("## Metrics Summary")
    lines.append("")
    lines.append(summary.to_markdown())
    lines.append("")
    lines.append("## Ranking")
    lines.append("")
    lines.append(ranking.to_markdown(index=False))
    lines.append("")
    lines.append("## Pareto Set")
    lines.append("")
    lines.append(pareto.to_markdown(index=False))
    output_dir.joinpath("report.md").write_text("\n".join(lines), encoding="utf-8")


def write_comparison_report(
    output_dir: Path,
    summary: pd.DataFrame,
    ranking: pd.DataFrame,
    pareto: pd.DataFrame,
) -> None:
    lines = ["# PEA Strategy Comparison", "", "## Metrics Summary", ""]
    lines.append(summary.to_markdown(index=False))
    lines.append("")
    lines.append("## Ranking")
    lines.append("")
    lines.append(ranking.to_markdown(index=False))
    lines.append("")
    lines.append("## Pareto Set")
    lines.append("")
    lines.append(pareto.to_markdown(index=False))
    output_dir.joinpath("report.md").write_text("\n".join(lines), encoding="utf-8")
