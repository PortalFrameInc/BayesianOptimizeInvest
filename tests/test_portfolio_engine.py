import numpy as np

from invest_sim.config.schemas import (
    CorrelationConfig,
    CostModelConfig,
    MarketPaths,
    SimulationConfig,
    StrategyConfig,
    UniverseConfig,
)
from invest_sim.portfolio import simulate_portfolio


def test_portfolio_invariants():
    market_paths = MarketPaths(
        returns=np.full((10, 1, 5), 0.001),
        asset_ids=["WORLD"],
    )
    universe = UniverseConfig(
        assets=[{"id": "WORLD", "mu_annual": 0.07, "sigma_annual": 0.15, "ter_annual": 0.0}],
        correlations=CorrelationConfig(matrix=[[1.0]]),
        leveraged_assets=None,
    )
    strategy = StrategyConfig(
        name="test",
        target_weights={"WORLD": 1.0},
        constraints={"max_weight": 1.0, "allow_cash": False},
        overlays={
            "vol_targeting": {
                "enabled": False,
                "target_vol_annual": 0.12,
                "lookback_days": 63,
                "max_leverage_multiplier": 1.0,
                "min_leverage_multiplier": 0.0,
            }
        },
    )
    cost_model = CostModelConfig(
        broker={"model": "bps_notional", "fixed_fee_eur": 0.0, "bps": 0.0},
        slippage_bps=0.0,
        ter_accrual="daily",
        min_trade_eur=0.0,
    )
    sim_config = SimulationConfig(
        run_name="test",
        time_step="D",
        n_years=1,
        trading_days_per_year=252,
        n_paths=5,
        seed=1,
        initial_capital_eur=1000.0,
        contributions={"enabled": False, "monthly_amount_eur": 0.0, "day_of_month": 1},
        rebalancing={"frequency": "none", "threshold_abs": 0.0},
        output={"base_dir": "runs", "save_nav_paths": False, "save_weights_paths": True, "save_turnover_paths": True},
    )

    portfolio = simulate_portfolio(
        market_paths,
        universe,
        strategy,
        cost_model,
        sim_config,
    )

    assert (portfolio.nav > 0).all()
    assert portfolio.weights is not None
    weights_sum = portfolio.weights.sum(axis=1)
    assert np.allclose(weights_sum, 1.0, atol=1e-6)
    assert portfolio.turnover is not None
    assert (portfolio.turnover >= 0).all()
