from __future__ import annotations

from pathlib import Path
from typing import Type, TypeVar

import yaml

from pea_sim.config import schemas

ConfigType = TypeVar("ConfigType")


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_config(path: Path, model: Type[ConfigType]) -> ConfigType:
    data = load_yaml(path)
    return model.model_validate(data)


def load_simulation(path: Path) -> schemas.SimulationConfig:
    return load_config(path, schemas.SimulationConfig)


def load_universe(path: Path) -> schemas.UniverseConfig:
    return load_config(path, schemas.UniverseConfig)


def load_cost_model(path: Path) -> schemas.CostModelConfig:
    return load_config(path, schemas.CostModelConfig)


def load_market_model(path: Path) -> schemas.MarketModelConfig:
    data = load_yaml(path)
    model_type = data.get("model_type")
    if model_type == "student_t":
        return schemas.StudentTConfig.model_validate(data)
    if model_type == "regimes":
        return schemas.RegimesConfig.model_validate(data)
    return schemas.MarketModelConfig.model_validate(data)


def load_strategy(path: Path) -> schemas.StrategyConfig:
    return load_config(path, schemas.StrategyConfig)
