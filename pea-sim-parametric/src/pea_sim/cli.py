from __future__ import annotations

from pathlib import Path

import typer

from pea_sim.config import load_cost_model, load_market_model, load_simulation, load_strategy, load_universe
from pea_sim.experiments.compare import compare_strategies
from pea_sim.experiments.run import run_experiment

app = typer.Typer(help="PEA parametric Monte Carlo simulator")


def _validate_configs(
    base: Path,
    universe: Path,
    cost: Path,
    market: Path,
    strategy: Path | None,
) -> None:
    load_simulation(base)
    load_universe(universe)
    load_cost_model(cost)
    load_market_model(market)
    if strategy is not None:
        load_strategy(strategy)


@app.command()
def validate(
    base: Path = typer.Option(..., exists=True, dir_okay=False),
    universe: Path = typer.Option(..., exists=True, dir_okay=False),
    cost: Path = typer.Option(..., exists=True, dir_okay=False),
    market: Path = typer.Option(..., exists=True, dir_okay=False),
    strategy: Path = typer.Option(None, exists=True, dir_okay=False),
) -> None:
    """Validate configuration files."""
    _validate_configs(base, universe, cost, market, strategy)
    typer.echo("Configs validated successfully.")


@app.command()
def run(
    base: Path = typer.Option(..., exists=True, dir_okay=False),
    universe: Path = typer.Option(..., exists=True, dir_okay=False),
    cost: Path = typer.Option(..., exists=True, dir_okay=False),
    market: Path = typer.Option(..., exists=True, dir_okay=False),
    strategy: Path = typer.Option(..., exists=True, dir_okay=False),
) -> None:
    """Run a single strategy experiment."""
    result = run_experiment(base, universe, cost, market, strategy)
    typer.echo(f"Run completed: {result.output_dir}")


@app.command()
def compare(
    base: Path = typer.Option(..., exists=True, dir_okay=False),
    universe: Path = typer.Option(..., exists=True, dir_okay=False),
    cost: Path = typer.Option(..., exists=True, dir_okay=False),
    market: Path = typer.Option(..., exists=True, dir_okay=False),
    strategies_dir: Path = typer.Option(..., exists=True, file_okay=False),
) -> None:
    """Compare all strategies in a directory."""
    result = compare_strategies(base, universe, cost, market, strategies_dir)
    typer.echo(f"Comparison completed: {result.output_dir}")


if __name__ == "__main__":
    app()
