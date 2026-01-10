from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict


class Strategy(ABC):
    @abstractmethod
    def target_weights(self) -> Dict[str, float]:
        raise NotImplementedError
