from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from invest_sim.strategies.base import Strategy


@dataclass
class StaticStrategy(Strategy):
    weights: Dict[str, float]

    def target_weights(self) -> Dict[str, float]:
        return self.weights
