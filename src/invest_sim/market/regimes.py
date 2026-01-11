from __future__ import annotations

import numpy as np

from invest_sim.config.schemas import MarketPaths, RegimesConfig, SimulationConfig, UniverseConfig
from invest_sim.market.base import FittedMarketModel, MarketModel


def _nearest_pd(matrix: np.ndarray, epsilon: float = 1e-6) -> np.ndarray:
    sym = (matrix + matrix.T) / 2
    eigvals, eigvecs = np.linalg.eigh(sym)
    eigvals = np.maximum(eigvals, epsilon)
    pd = eigvecs @ np.diag(eigvals) @ eigvecs.T
    d = np.sqrt(np.diag(pd))
    return pd / np.outer(d, d)


def _adjust_corr(base_corr: np.ndarray, multiplier: float) -> np.ndarray:
    corr = base_corr.copy()
    n = corr.shape[0]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            corr[i, j] = np.clip(corr[i, j] * multiplier, -0.99, 0.99)
    corr = (corr + corr.T) / 2
    corr[np.diag_indices_from(corr)] = 1.0
    if np.any(np.linalg.eigvalsh(corr) <= 0):
        corr = _nearest_pd(corr)
    return corr


class RegimeSwitchingModel(MarketModel):
    def fit(
        self,
        universe_config: UniverseConfig,
        market_model_config: RegimesConfig,
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
        regime_params = {
            "regimes": market_model_config.regimes,
            "transition_matrix": np.array(market_model_config.transition_matrix, dtype=float),
            "initial_probs": np.array(market_model_config.initial_probs, dtype=float),
            "base_corr": corr,
            "mu_daily": mu_daily,
            "sigma_daily": sigma_daily,
        }
        return FittedMarketModel(
            asset_ids=asset_ids,
            mu_daily=mu_daily,
            cov_daily=cov_daily,
            model_config=market_model_config,
            regime_params=regime_params,
        )

    def sample_paths(
        self, fitted_model: FittedMarketModel, sim_config: SimulationConfig
    ) -> MarketPaths:
        t_steps = sim_config.n_years * sim_config.trading_days_per_year
        n_assets = len(fitted_model.asset_ids)
        n_paths = sim_config.n_paths
        rng = np.random.default_rng(sim_config.seed)
        params = fitted_model.regime_params
        regimes = params["regimes"]
        transition = params["transition_matrix"]
        initial_probs = params["initial_probs"]
        mu_daily = params["mu_daily"]
        sigma_daily = params["sigma_daily"]
        base_corr = params["base_corr"]

        regime_index = np.zeros((t_steps, n_paths), dtype=int)
        regime_index[0] = rng.choice(len(regimes), size=n_paths, p=initial_probs)
        for t in range(1, t_steps):
            prev = regime_index[t - 1]
            for k in range(len(regimes)):
                mask = prev == k
                if np.any(mask):
                    regime_index[t, mask] = rng.choice(len(regimes), size=mask.sum(), p=transition[k])

        returns = np.zeros((t_steps, n_assets, n_paths))
        for k, regime in enumerate(regimes):
            corr = _adjust_corr(base_corr, regime.corr_multiplier)
            sigma_adj = sigma_daily * regime.sigma_multiplier
            mu_adj = mu_daily * regime.mu_multiplier
            cov = np.outer(sigma_adj, sigma_adj) * corr
            chol = np.linalg.cholesky(cov)
            normals = rng.standard_normal(size=(t_steps, n_assets, n_paths))
            regime_mask = regime_index == k
            if not np.any(regime_mask):
                continue
            day_indices = np.where(regime_mask)
            returns[day_indices[0], :, day_indices[1]] = (
                np.einsum("ij,tjp->tip", chol, normals)[day_indices[0], :, day_indices[1]]
                + mu_adj[None, :]
            )
        return MarketPaths(returns=returns, asset_ids=fitted_model.asset_ids, regime=regime_index)
