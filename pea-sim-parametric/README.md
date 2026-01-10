# PEA Sim Paramétrique

Simulation paramétrique Monte-Carlo d'un portefeuille de type PEA français. Le simulateur utilise des rendements journaliers basés sur des modèles (**GBM**, **Student-t**, ou **régimes**) sans données de marché externes ni calibration historique. Il prend en charge des allocations statiques, le rééquilibrage, les contributions, et les ETF à effet de levier avec remise à zéro quotidienne, et produit des exécutions reproductibles avec graphiques et métriques.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Démarrage rapide

Valider les configurations :

```bash
pea-sim validate \
  --base configs/base.yaml \
  --universe configs/universe.yaml \
  --cost configs/cost_model.yaml \
  --market configs/market_models/regimes.yaml \
  --strategy configs/strategies/buy_and_hold_world.yaml
```

Lancer une stratégie unique :

```bash
pea-sim run \
  --base configs/base.yaml \
  --universe configs/universe.yaml \
  --cost configs/cost_model.yaml \
  --market configs/market_models/regimes.yaml \
  --strategy configs/strategies/buy_and_hold_world.yaml
```

Comparer toutes les stratégies :

```bash
pea-sim compare \
  --base configs/base.yaml \
  --universe configs/universe.yaml \
  --cost configs/cost_model.yaml \
  --market configs/market_models/regimes.yaml \
  --strategies-dir configs/strategies
```

## Notes et hypothèses

- Tous les modèles sont paramétriques : **aucune donnée historique** n'est chargée ni calibrée dans ce projet.
- Des pas de temps journaliers sont utilisés en interne, en particulier lorsque la levier est présente.
- Les actifs à effet de levier sont calculés à partir des rendements sous-jacents en utilisant une remise à zéro quotidienne :
  `r_L = leverage * r_underlying - fee_daily`.
- Le ciblage de volatilité n'emprunte jamais de façon synthétique. Si la stratégie ne contient pas déjà d'actifs à effet de levier, tout levier demandé au-dessus de 1.0 est limité à 1.0.

## Sorties

Chaque exécution écrit un dossier horodaté dans `runs/` contenant :

- `config_snapshot/` copies YAML
- `nav_paths.npy`
- `metrics_per_path.csv`
- `metrics_summary.csv`
- `plots/*.png`
- `report.md`
