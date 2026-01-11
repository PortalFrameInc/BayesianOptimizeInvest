import numpy as np

from invest_sim.config.schemas import (
    CorrelationConfig,
    MarketModelConfig,
    RegimeConfig,
    RegimesConfig,
    SimulationConfig,
    StudentTConfig,
    UniverseConfig,
)
from invest_sim.market.gbm import GBMModel
from invest_sim.market.regimes import RegimeSwitchingModel
from invest_sim.market.student_t import StudentTModel


def _universe():
    return UniverseConfig(
        assets=[
            {"id": "WORLD", "mu_annual": 0.07, "sigma_annual": 0.15, "ter_annual": 0.0},
            {"id": "SP500", "mu_annual": 0.075, "sigma_annual": 0.16, "ter_annual": 0.0},
        ],
        correlations=CorrelationConfig(matrix=[[1.0, 0.9], [0.9, 1.0]]),
        leveraged_assets=None,
    )


def _sim_config():
    return SimulationConfig(
        run_name="test",
        time_step="D",
        n_years=1,
        trading_days_per_year=252,
        n_paths=200,
        seed=42,
        initial_capital_eur=1000.0,
        contributions={"enabled": False, "monthly_amount_eur": 0.0, "day_of_month": 1},
        rebalancing={"frequency": "none", "threshold_abs": 0.0},
        output={"base_dir": "runs", "save_nav_paths": False, "save_weights_paths": False, "save_turnover_paths": False},
    )


def test_gbm_model_shapes():
    sim_config = _sim_config()
    universe = _universe()
    market_config = MarketModelConfig(model_type="gbm", enabled_assets=["WORLD", "SP500"])
    model = GBMModel()
    fitted = model.fit(universe, market_config, sim_config)
    paths = model.sample_paths(fitted, sim_config)
    assert paths.returns.shape == (252, 2, 200)
    assert np.isfinite(paths.returns).all()
    assert np.std(paths.returns) > 0


def test_student_t_model_shapes():
    sim_config = _sim_config()
    universe = _universe()
    market_config = StudentTConfig(model_type="student_t", enabled_assets=["WORLD", "SP500"], df=6.0)
    model = StudentTModel()
    fitted = model.fit(universe, market_config, sim_config)
    paths = model.sample_paths(fitted, sim_config)
    assert paths.returns.shape == (252, 2, 200)
    assert np.isfinite(paths.returns).all()
    assert np.std(paths.returns) > 0


def test_regime_model_shapes():
    sim_config = _sim_config()
    universe = _universe()
    market_config = RegimesConfig(
        model_type="regimes",
        enabled_assets=["WORLD", "SP500"],
        regimes=[
            RegimeConfig(name="calm", mu_multiplier=1.0, sigma_multiplier=1.0, corr_multiplier=1.0),
            RegimeConfig(name="crisis", mu_multiplier=0.0, sigma_multiplier=2.0, corr_multiplier=1.2),
        ],
        transition_matrix=[[0.9, 0.1], [0.2, 0.8]],
        initial_probs=[0.8, 0.2],
    )
    model = RegimeSwitchingModel()
    fitted = model.fit(universe, market_config, sim_config)
    paths = model.sample_paths(fitted, sim_config)
    assert paths.returns.shape == (252, 2, 200)
    assert paths.regime is not None
    assert paths.regime.shape == (252, 200)
    assert np.isfinite(paths.returns).all()
