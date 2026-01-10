from __future__ import annotations

from dataclasses import dataclass

from pea_sim.config.schemas import CostModelConfig


@dataclass(frozen=True)
class TransactionCostResult:
    total_cost: float
    n_orders: int


def compute_transaction_costs(cost_model: CostModelConfig, traded_notional: float, n_orders: int) -> TransactionCostResult:
    broker_cost = 0.0
    if cost_model.broker.model == "fixed_per_order":
        broker_cost = n_orders * cost_model.broker.fixed_fee_eur
    elif cost_model.broker.model == "bps_notional":
        broker_cost = traded_notional * (cost_model.broker.bps / 1e4)
    slippage_cost = traded_notional * (cost_model.slippage_bps / 1e4)
    return TransactionCostResult(total_cost=broker_cost + slippage_cost, n_orders=n_orders)
