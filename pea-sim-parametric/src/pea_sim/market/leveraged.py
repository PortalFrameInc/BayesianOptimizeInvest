from __future__ import annotations

import numpy as np


def compute_leveraged_returns(
    underlying_returns: np.ndarray,
    leverage: float,
    fee_annual: float,
    trading_days_per_year: int,
) -> np.ndarray:
    fee_daily = fee_annual / trading_days_per_year
    return leverage * underlying_returns - fee_daily
