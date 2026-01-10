from pathlib import Path

import yaml

from pea_sim.experiments.run import run_experiment


def test_end_to_end_run(tmp_path: Path):
    base = Path("configs/base.yaml")
    universe = Path("configs/universe.yaml")
    cost = Path("configs/cost_model.yaml")
    market = Path("configs/market_models/gbm.yaml")
    strategy = Path("configs/strategies/buy_and_hold_world.yaml")

    base_data = yaml.safe_load(base.read_text(encoding="utf-8"))
    base_data["n_years"] = 1
    base_data["n_paths"] = 50
    base_data["output"]["base_dir"] = str(tmp_path)
    temp_base = tmp_path / "base.yaml"
    temp_base.write_text(yaml.safe_dump(base_data), encoding="utf-8")

    result = run_experiment(temp_base, universe, cost, market, strategy)

    assert result.output_dir.exists()
    assert (result.output_dir / "config_snapshot").exists()
    assert (result.output_dir / "metrics_per_path.csv").exists()
    assert (result.output_dir / "metrics_summary.csv").exists()
    assert (result.output_dir / "plots" / "nav_fanchart.png").exists()
    assert (result.output_dir / "report.md").exists()
