from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

import numpy as np

from invest_sim.config.schemas import MarketModelConfig, MarketPaths, SimulationConfig, UniverseConfig


@dataclass(frozen=True)
class FittedMarketModel:
    asset_ids: List[str]
    mu_daily: np.ndarray
    cov_daily: np.ndarray
    model_config: MarketModelConfig
    regime_params: Optional[dict] = None


class MarketModel(ABC):
    @abstractmethod
    def fit(
        self,
        universe_config: UniverseConfig,
        market_model_config: MarketModelConfig,
        sim_config: SimulationConfig,
    ) -> FittedMarketModel:
        raise NotImplementedError

    @abstractmethod
    def sample_paths(
        self, fitted_model: FittedMarketModel, sim_config: SimulationConfig
    ) -> MarketPaths:
        raise NotImplementedError
