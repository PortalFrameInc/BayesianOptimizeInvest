from __future__ import annotations

import numpy as np

from invest_sim.config.schemas import MarketModelConfig, MarketPaths, SimulationConfig, UniverseConfig
from invest_sim.market.base import FittedMarketModel, MarketModel


class GBMModel(MarketModel):
    def fit(
        self,
        universe_config: UniverseConfig,
        market_model_config: MarketModelConfig,
        sim_config: SimulationConfig,
    ) -> FittedMarketModel:
        asset_ids = market_model_config.enabled_assets
        universe_assets = {asset.id: asset for asset in universe_config.assets}
        asset_order = [asset.id for asset in universe_config.assets]
        mu_annual = np.array([universe_assets[asset].mu_annual for asset in asset_ids])
        sigma_annual = np.array([universe_assets[asset].sigma_annual for asset in asset_ids])
        corr = np.array(universe_config.correlations.matrix)
        indices = [asset_order.index(asset_id) for asset_id in asset_ids]
        corr = corr[np.ix_(indices, indices)]
        trading_days = sim_config.trading_days_per_year
        mu_daily = mu_annual / trading_days
        sigma_daily = sigma_annual / np.sqrt(trading_days)
        cov_daily = np.outer(sigma_daily, sigma_daily) * corr
        return FittedMarketModel(
            asset_ids=asset_ids,
            mu_daily=mu_daily,
            cov_daily=cov_daily,
            model_config=market_model_config,
        )

    def sample_paths(
        self, fitted_model: FittedMarketModel, sim_config: SimulationConfig
    ) -> MarketPaths:
        t_steps = sim_config.n_years * sim_config.trading_days_per_year
        n_assets = len(fitted_model.asset_ids)
        n_paths = sim_config.n_paths
        rng = np.random.default_rng(sim_config.seed)
        chol = np.linalg.cholesky(fitted_model.cov_daily)
        normals = rng.standard_normal(size=(t_steps, n_assets, n_paths))
        returns = np.einsum("ij,tjp->tip", chol, normals) + fitted_model.mu_daily[:, None]
        return MarketPaths(returns=returns, asset_ids=fitted_model.asset_ids)
