from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd


def _format_table(df: pd.DataFrame, *, index: bool) -> str:
    try:
        return df.to_markdown(index=index)
    except ImportError:
        return df.to_string(index=index)


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
    lines.append(_format_table(summary, index=True))
    lines.append("")
    lines.append("## Ranking")
    lines.append("")
    lines.append(_format_table(ranking, index=False))
    lines.append("")
    lines.append("## Pareto Set")
    lines.append("")
    lines.append(_format_table(pareto, index=False))
    output_dir.joinpath("report.md").write_text("\n".join(lines), encoding="utf-8")


def write_comparison_report(
    output_dir: Path,
    summary: pd.DataFrame,
    ranking: pd.DataFrame,
    pareto: pd.DataFrame,
    base_config: Dict = None,
) -> None:
    lines = ["# PEA Strategy Comparison", ""]
    
    if base_config:
        lines.append("## Simulation Parameters")
        lines.append("")
        lines.append(f"- **Horizon**: {base_config.get('n_years', 'N/A')} years")
        lines.append(f"- **Number of paths**: {base_config.get('n_paths', 'N/A'):,}")
        lines.append(f"- **Initial capital**: {base_config.get('initial_capital_eur', 'N/A'):,} EUR")
        lines.append(f"- **Time step**: {base_config.get('time_step', 'N/A')}")
        lines.append(f"- **Trading days per year**: {base_config.get('trading_days_per_year', 'N/A')}")
        
        if 'seed' in base_config and base_config['seed'] is not None:
            lines.append(f"- **Seed**: {base_config['seed']}")
        
        rebal = base_config.get('rebalancing', {})
        if rebal:
            lines.append(f"- **Rebalancing**: {rebal.get('frequency', 'N/A')} (threshold: {rebal.get('threshold_abs', 'N/A')})")
        
        contrib = base_config.get('contributions', {})
        if contrib and contrib.get('enabled'):
            lines.append(f"- **Monthly contributions**: {contrib.get('monthly_amount_eur', 'N/A')} EUR")
        
        lines.append("")
    
    lines.append("## Metrics Summary")
    lines.append("")
    lines.append(_format_table(summary, index=False))
    lines.append("")
    lines.append("## Ranking")
    lines.append("")
    lines.append(_format_table(ranking, index=False))
    lines.append("")
    lines.append("## Pareto Set")
    lines.append("")
    lines.append(_format_table(pareto, index=False))
    output_dir.joinpath("report.md").write_text("\n".join(lines), encoding="utf-8")