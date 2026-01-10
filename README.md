# PEA Sim (Paramétrique)

Simulateur Monte-Carlo pour un portefeuille ETF de type PEA français utilisant des **modèles de marché paramétriques** (aucune série temporelle historique dans le MVP). Le projet compare des stratégies (allocation, rééquilibrage, apports, ETFs à effet de levier avec remise à zéro quotidienne) et produit des métriques et graphiques automatisés.

## Portée (MVP)

- Simulation avec pas de temps journalier (252 jours de bourse / an)
- Modèles de marché : GBM multivarié, Student-t multivarié, chaînes de Markov (calme/crise)
- Moteur de portefeuille : allocation initiale, apports mensuels (approximatifs), rééquilibrage, coûts de transaction, provision quotidienne du TER
- ETFs à effet de levier : calculés à partir des rendements sous-jacents journaliers avec remise à zéro quotidienne + frais
- Sorties : trajectoires de NAV, métriques par trajectoire, métriques récapitulatives, graphiques, classement + ensemble de Pareto

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

## Validation des configurations

```bash
pea-sim validate \
  --base configs/base.yaml \
  --universe configs/universe.yaml \
  --cost configs/cost_model.yaml \
  --market configs/market_models/regimes.yaml \
  --strategy configs/strategies/buy_and_hold_world.yaml
```

## Lancer une stratégie unique

```bash
pea-sim run \
  --base configs/base.yaml \
  --universe configs/universe.yaml \
  --cost configs/cost_model.yaml \
  --market configs/market_models/regimes.yaml \
  --strategy configs/strategies/buy_and_hold_world.yaml
```

## Comparer toutes les stratégies d'un répertoire

```bash
pea-sim compare \
  --base configs/base.yaml \
  --universe configs/universe.yaml \
  --cost configs/cost_model.yaml \
  --market configs/market_models/regimes.yaml \
  --strategies-dir configs/strategies/
```

## Sorties

Chaque exécution crée un dossier sous `runs/` :

- `config_snapshot/` (YAML utilisés)
- `nav_paths.npy` (optionnel)
- `metrics_per_path.csv`, `metrics_summary.csv`
- `plots/` (fan chart, CDFs, nuages de points)
- `report.md` (résumé + classement)

## Notes / limitations

Ce MVP est un cadre d'analyse de scénarios : les résultats dépendent des paramètres choisis (drift, volatilité, corrélations, comportement des régimes). Ce n'est pas un backtest historique. Une phase ultérieure peut ajouter l'ingestion de données et la calibration sur des séries temporelles réelles sans changer les interfaces principales.
