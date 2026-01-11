from __future__ import annotations

from pathlib import Path

import typer

from invest_sim.config import load_cost_model, load_market_model, load_simulation, load_strategy, load_universe
from invest_sim.experiments.compare import compare_strategies
from invest_sim.experiments.run import run_experiment

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
    strategies_dir: Path = typer.Option(..., exists=True, file_okay=False),
) -> None:
    """Validate configuration files."""

    failures: list[tuple[Path, Exception]] = []
    files = sorted([p for ext in ("*.yaml", "*.yml") for p in strategies_dir.rglob(ext)])
    if not files:
        typer.echo("No strategy YAML files found in the directory.")
        raise typer.Exit(code=1)
    for f in files:
        try:
            _validate_configs(base, universe, cost, market, f)
            typer.echo(f"Validated {f.relative_to(strategies_dir)}")
        except Exception as e:  # capture validation error per file
            failures.append((f, e))
            typer.secho(f"FAILED {f.relative_to(strategies_dir)}: {e}", fg="red")

    if failures:
        typer.secho(f"{len(failures)} strategy files failed validation.", fg="red")
        raise typer.Exit(code=1)

    typer.echo("All strategies validated successfully.")


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
