from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RebalanceOrder:
    asset_id: str
    notional: float
