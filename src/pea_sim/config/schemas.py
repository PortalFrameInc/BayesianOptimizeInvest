from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np
from pydantic import BaseModel, Field, field_validator, model_validator


class ContributionsConfig(BaseModel):
    enabled: bool
    monthly_amount_eur: float = Field(ge=0)
    day_of_month: int = Field(ge=1, le=28)


class RebalancingConfig(BaseModel):
    frequency: str = Field(pattern=r"^(none|monthly|quarterly|annual)$")
    threshold_abs: float = Field(ge=0)


class OutputConfig(BaseModel):
    base_dir: str = "runs"
    save_nav_paths: bool = True
    save_weights_paths: bool = False
    save_turnover_paths: bool = False


class SimulationConfig(BaseModel):
    run_name: str
    time_step: str
    n_years: int = Field(ge=1)
    trading_days_per_year: int = 252
    n_paths: int = Field(ge=1)
    seed: int
    initial_capital_eur: float = Field(gt=0)
    contributions: ContributionsConfig
    rebalancing: RebalancingConfig
    output: OutputConfig

    @field_validator("time_step")
    @classmethod
    def validate_time_step(cls, value: str) -> str:
        if value != "D":
            raise ValueError("time_step must be 'D' for daily")
        return value


class BaseAssetConfig(BaseModel):
    id: str
    mu_annual: float
    sigma_annual: float = Field(gt=0)
    ter_annual: float = Field(ge=0)


class LeveragedAssetConfig(BaseModel):
    id: str
    underlying_id: str
    leverage: float
    extra_fee_annual: float = Field(ge=0)


class CorrelationConfig(BaseModel):
    matrix: List[List[float]]

    @field_validator("matrix")
    @classmethod
    def validate_matrix(cls, value: List[List[float]]) -> List[List[float]]:
        matrix = np.array(value, dtype=float)
        if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
            raise ValueError("correlation matrix must be square")
        if not np.allclose(matrix, matrix.T, atol=1e-6):
            raise ValueError("correlation matrix must be symmetric")
        if not np.allclose(np.diag(matrix), 1.0, atol=1e-6):
            raise ValueError("correlation matrix diagonal must be 1.0")
        eigvals = np.linalg.eigvalsh(matrix)
        if np.any(eigvals <= 0):
            raise ValueError("correlation matrix must be positive definite")
        return value


class UniverseConfig(BaseModel):
    assets: List[BaseAssetConfig]
    correlations: CorrelationConfig
    leveraged_assets: Optional[List[LeveragedAssetConfig]] = None

    @model_validator(mode="after")
    def validate_assets(self) -> "UniverseConfig":
        asset_ids = [asset.id for asset in self.assets]
        if len(asset_ids) != len(set(asset_ids)):
            raise ValueError("asset ids must be unique")
        if self.leveraged_assets:
            for lev in self.leveraged_assets:
                if lev.underlying_id not in asset_ids:
                    raise ValueError(
                        f"leveraged asset {lev.id} references unknown underlying {lev.underlying_id}"
                    )
        n_assets = len(self.assets)
        corr = np.array(self.correlations.matrix)
        if corr.shape != (n_assets, n_assets):
            raise ValueError("correlation matrix size must match assets list")
        return self


class BrokerConfig(BaseModel):
    model: str = Field(pattern=r"^(fixed_per_order|bps_notional)$")
    fixed_fee_eur: float = Field(ge=0)
    bps: float = Field(ge=0)


class CostModelConfig(BaseModel):
    broker: BrokerConfig
    slippage_bps: float = Field(ge=0)
    ter_accrual: str
    min_trade_eur: float = Field(ge=0)

    @field_validator("ter_accrual")
    @classmethod
    def validate_ter(cls, value: str) -> str:
        if value != "daily":
            raise ValueError("ter_accrual must be 'daily'")
        return value


class MarketModelConfig(BaseModel):
    model_type: str = Field(pattern=r"^(gbm|student_t|regimes)$")
    enabled_assets: List[str]

    @field_validator("enabled_assets")
    @classmethod
    def validate_enabled_assets(cls, value: List[str]) -> List[str]:
        if len(value) != len(set(value)):
            raise ValueError("enabled_assets must be unique")
        return value


class StudentTConfig(MarketModelConfig):
    df: float = Field(gt=2)


class RegimeConfig(BaseModel):
    name: str
    mu_multiplier: float
    sigma_multiplier: float = Field(gt=0)
    corr_multiplier: float = Field(ge=0)


class RegimesConfig(MarketModelConfig):
    regimes: List[RegimeConfig]
    transition_matrix: List[List[float]]
    initial_probs: List[float]

    @model_validator(mode="after")
    def validate_regimes(self) -> "RegimesConfig":
        k = len(self.regimes)
        tm = np.array(self.transition_matrix, dtype=float)
        if tm.shape != (k, k):
            raise ValueError("transition_matrix shape must be (K,K)")
        if not np.allclose(tm.sum(axis=1), 1.0, atol=1e-6):
            raise ValueError("transition_matrix rows must sum to 1")
        probs = np.array(self.initial_probs, dtype=float)
        if probs.shape != (k,):
            raise ValueError("initial_probs must be length K")
        if not np.isclose(probs.sum(), 1.0, atol=1e-6):
            raise ValueError("initial_probs must sum to 1")
        return self


class VolTargetingConfig(BaseModel):
    enabled: bool
    target_vol_annual: float = Field(gt=0)
    lookback_days: int = Field(ge=20)
    max_leverage_multiplier: float = Field(ge=1)
    min_leverage_multiplier: float = Field(ge=0)


class ConstraintsConfig(BaseModel):
    max_weight: float = Field(le=1)
    allow_cash: bool


class OverlaysConfig(BaseModel):
    vol_targeting: VolTargetingConfig


class StrategyConfig(BaseModel):
    name: str
    target_weights: Dict[str, float]
    constraints: ConstraintsConfig
    overlays: OverlaysConfig

    @model_validator(mode="after")
    def validate_weights(self) -> "StrategyConfig":
        weights = self.target_weights
        if any(weight < 0 for weight in weights.values()):
            raise ValueError("target weights must be non-negative")
        total = sum(weights.values())
        if self.constraints.allow_cash:
            if total > 1.0 + 1e-6:
                raise ValueError("target weights must sum to <= 1.0 when allow_cash true")
        else:
            if not np.isclose(total, 1.0, atol=1e-6):
                raise ValueError("target weights must sum to 1.0 when allow_cash false")
        if any(weight > self.constraints.max_weight + 1e-6 for weight in weights.values()):
            raise ValueError("target weight exceeds max_weight")
        return self


@dataclass
class MarketPaths:
    returns: np.ndarray
    asset_ids: List[str]
    regime: Optional[np.ndarray] = None


@dataclass
class PortfolioPaths:
    nav: np.ndarray
    asset_ids: List[str]
    weights: Optional[np.ndarray] = None
    turnover: Optional[np.ndarray] = None
