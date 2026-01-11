from pathlib import Path

from invest_sim.config import load_cost_model, load_market_model, load_simulation, load_strategy, load_universe


def test_configs_load():
    base = Path("configs/base.yaml")
    universe = Path("configs/universe.yaml")
    cost = Path("configs/cost_model.yaml")
    market_gbm = Path("configs/market_models/gbm.yaml")
    market_student = Path("configs/market_models/student_t.yaml")
    market_regimes = Path("configs/market_models/regimes.yaml")
    strategies = Path("configs/strategies")

    load_simulation(base)
    load_universe(universe)
    load_cost_model(cost)
    load_market_model(market_gbm)
    load_market_model(market_student)
    load_market_model(market_regimes)
    for path in strategies.glob("*.yaml"):
        load_strategy(path)
