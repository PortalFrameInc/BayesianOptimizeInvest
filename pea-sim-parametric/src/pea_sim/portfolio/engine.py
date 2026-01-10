from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from pea_sim.config.schemas import (
    CostModelConfig,
    MarketPaths,
    PortfolioPaths,
    SimulationConfig,
    StrategyConfig,
    UniverseConfig,
)
from pea_sim.market.leveraged import compute_leveraged_returns
from pea_sim.portfolio.costs import compute_transaction_costs


@dataclass
class AssetUniverse:
    asset_ids: List[str]
    base_asset_ids: List[str]
    leveraged_asset_ids: List[str]
    cash_included: bool


def _build_asset_universe(
    market_paths: MarketPaths, universe: UniverseConfig, strategy: StrategyConfig
) -> Tuple[AssetUniverse, Dict[str, int]]:
    base_asset_ids = market_paths.asset_ids
    leveraged_asset_ids = [asset.id for asset in (universe.leveraged_assets or [])]
    asset_ids = base_asset_ids + leveraged_asset_ids
    if strategy.constraints.allow_cash:
        asset_ids.append("CASH")
    index = {asset_id: idx for idx, asset_id in enumerate(asset_ids)}
    return (
        AssetUniverse(
            asset_ids=asset_ids,
            base_asset_ids=base_asset_ids,
            leveraged_asset_ids=leveraged_asset_ids,
            cash_included=strategy.constraints.allow_cash,
        ),
        index,
    )


def _target_weights_vector(
    universe: AssetUniverse, strategy: StrategyConfig
) -> np.ndarray:
    weights = np.zeros(len(universe.asset_ids))
    for asset_id, weight in strategy.target_weights.items():
        if asset_id not in universe.asset_ids:
            raise ValueError(f"strategy references unknown asset {asset_id}")
        weights[universe.asset_ids.index(asset_id)] = weight
    if universe.cash_included:
        cash_index = universe.asset_ids.index("CASH")
        weights[cash_index] = max(0.0, 1.0 - weights.sum())
    return weights


def _should_rebalance(
    step: int, sim_config: SimulationConfig, strategy: StrategyConfig
) -> bool:
    freq = sim_config.rebalancing.frequency
    if freq == "none":
        return False
    if freq == "monthly":
        return step % 21 == 0
    if freq == "quarterly":
        return step % 63 == 0
    if freq == "annual":
        return step % sim_config.trading_days_per_year == 0
    return False


def _apply_vol_targeting(
    base_weights: np.ndarray,
    universe: AssetUniverse,
    strategy: StrategyConfig,
    realized_vol_annual: np.ndarray,
) -> np.ndarray:
    if not strategy.overlays.vol_targeting.enabled:
        return base_weights
    target_vol = strategy.overlays.vol_targeting.target_vol_annual
    scale = np.where(realized_vol_annual > 0, target_vol / realized_vol_annual, 1.0)
    scale = np.clip(
        scale,
        strategy.overlays.vol_targeting.min_leverage_multiplier,
        strategy.overlays.vol_targeting.max_leverage_multiplier,
    )
    risky_indices = [
        i for i, asset in enumerate(universe.asset_ids) if asset != "CASH"
    ]
    has_leveraged = any(
        asset_id in strategy.target_weights for asset_id in universe.leveraged_asset_ids
    )
    if not strategy.constraints.allow_cash:
        return base_weights
    if not has_leveraged:
        scale = np.minimum(scale, 1.0)
    scaled = base_weights.copy()
    scaled[risky_indices] = scaled[risky_indices] * scale
    cash_idx = universe.asset_ids.index("CASH") if universe.cash_included else None
    if cash_idx is not None:
        scaled[cash_idx] = np.maximum(0.0, 1.0 - scaled[risky_indices].sum(axis=0))
    return scaled


def simulate_portfolio(
    market_paths: MarketPaths,
    universe: UniverseConfig,
    strategy: StrategyConfig,
    cost_model: CostModelConfig,
    sim_config: SimulationConfig,
) -> PortfolioPaths:
    asset_universe, index_map = _build_asset_universe(market_paths, universe, strategy)
    t_steps, _, n_paths = market_paths.returns.shape
    asset_count = len(asset_universe.asset_ids)

    nav = np.zeros((t_steps + 1, n_paths))
    nav[0] = sim_config.initial_capital_eur
    holdings = np.zeros((asset_count, n_paths))

    base_weights = _target_weights_vector(asset_universe, strategy)
    holdings[:, :] = base_weights[:, None] * nav[0]

    weights = (
        np.zeros((t_steps + 1, asset_count, n_paths))
        if sim_config.output.save_weights_paths
        else None
    )
    turnover = (
        np.zeros((t_steps, n_paths)) if sim_config.output.save_turnover_paths else None
    )

    if weights is not None:
        weights[0] = base_weights[:, None]

    base_asset_ids = asset_universe.base_asset_ids
    base_asset_map = {asset_id: idx for idx, asset_id in enumerate(base_asset_ids)}

    leveraged_assets = {asset.id: asset for asset in (universe.leveraged_assets or [])}
    asset_config = {asset.id: asset for asset in universe.assets}

    lookback = strategy.overlays.vol_targeting.lookback_days
    port_ret_history = np.zeros((t_steps, n_paths))

    for t in range(t_steps):
        daily_returns = np.zeros((asset_count, n_paths))
        for asset_id in base_asset_ids:
            idx = index_map[asset_id]
            base_idx = base_asset_map[asset_id]
            asset = asset_config[asset_id]
            ter_daily = asset.ter_annual / sim_config.trading_days_per_year
            daily_returns[idx] = market_paths.returns[t, base_idx, :] - ter_daily

        for asset_id in asset_universe.leveraged_asset_ids:
            idx = index_map[asset_id]
            leveraged = leveraged_assets[asset_id]
            underlying_idx = base_asset_map[leveraged.underlying_id]
            underlying_returns = market_paths.returns[t, underlying_idx, :]
            fee_annual = asset_config[leveraged.underlying_id].ter_annual + leveraged.extra_fee_annual
            daily_returns[idx] = compute_leveraged_returns(
                underlying_returns,
                leverage=leveraged.leverage,
                fee_annual=fee_annual,
                trading_days_per_year=sim_config.trading_days_per_year,
            )

        holdings *= 1.0 + daily_returns
        nav[t + 1] = holdings.sum(axis=0)
        port_ret_history[t] = np.where(nav[t] > 0, nav[t + 1] / nav[t] - 1.0, 0.0)

        if sim_config.contributions.enabled:
            day_index = min(sim_config.contributions.day_of_month - 1, 20)
            if t % 21 == day_index:
                cash_idx = index_map.get("CASH")
                if cash_idx is not None:
                    holdings[cash_idx] += sim_config.contributions.monthly_amount_eur
                else:
                    nav[t + 1] += sim_config.contributions.monthly_amount_eur
                    holdings *= nav[t + 1] / holdings.sum(axis=0)

        if _should_rebalance(t, sim_config, strategy):
            realized_vol_annual = np.full(n_paths, np.nan)
            if strategy.overlays.vol_targeting.enabled and t >= lookback:
                window = port_ret_history[t - lookback + 1 : t + 1]
                realized_vol = np.std(window, axis=0, ddof=1)
                realized_vol_annual = realized_vol * np.sqrt(sim_config.trading_days_per_year)
            else:
                realized_vol_annual = np.full(n_paths, 0.0)

            target_weights = _apply_vol_targeting(
                base_weights[:, None], asset_universe, strategy, realized_vol_annual
            )
            current_nav = holdings.sum(axis=0)
            current_weights = np.where(current_nav > 0, holdings / current_nav, 0.0)
            diff = np.abs(current_weights - target_weights)
            if sim_config.rebalancing.threshold_abs == 0 or np.any(
                diff > sim_config.rebalancing.threshold_abs, axis=0
            ):
                target_values = target_weights * current_nav
                trades = target_values - holdings
                mask = np.abs(trades) >= cost_model.min_trade_eur
                trades = np.where(mask, trades, 0.0)
                traded_notional = np.sum(np.abs(trades), axis=0)
                n_orders = np.sum(trades != 0, axis=0)
                for p in range(n_paths):
                    cost = compute_transaction_costs(
                        cost_model, traded_notional[p], int(n_orders[p])
                    ).total_cost
                    cash_idx = index_map.get("CASH")
                    if cash_idx is not None:
                        holdings[cash_idx, p] -= cost
                    else:
                        holdings[:, p] *= (current_nav[p] - cost) / current_nav[p]
                holdings += trades
                if turnover is not None:
                    turnover[t] = np.where(current_nav > 0, traded_notional / current_nav, 0.0)

        if weights is not None:
            current_nav = holdings.sum(axis=0)
            weights[t + 1] = np.where(current_nav > 0, holdings / current_nav, 0.0)

    return PortfolioPaths(nav=nav, asset_ids=asset_universe.asset_ids, weights=weights, turnover=turnover)
