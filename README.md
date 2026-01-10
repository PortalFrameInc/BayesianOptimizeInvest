# PEA Sim (Paramétrique)

Simulation paramétrique Monte-Carlo appliqué à divers portefeuille. Le simulateur utilise des rendements journaliers basés sur des modèles (**GBM**, **Student-t**, ou **régimes**) sans données de marché externes ni calibration historique. Il prend en charge des allocations statiques, le rééquilibrage, les contributions, et les ETF à effet de levier avec remise à zéro quotidienne, et produit des exécutions reproductibles avec graphiques et métriques.

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
- Les actifs à effet de levier sont calculés à partir des rendements sous-jacents en utilisant une remise à zéro quotidienne : `r_L = leverage * r_underlying - fee_daily`.
- Le ciblage de volatilité n'emprunte jamais de façon synthétique. Si la stratégie ne contient pas déjà d'actifs à effet de levier, tout levier demandé au-dessus de 1.0 est limité à 1.0.

## Sorties

Chaque exécution créé un dossier horodaté dans `runs/` contenant :

- `config_snapshot/` copies YAML
- `nav_paths.npy`
- `metrics_per_path.csv`
- `metrics_summary.csv`
- `plots/*.png`
- `report.md`

## Déplacer le projet à la racine

Si vous souhaitez retirer le dossier `pea-sim-parametric` et remonter tout le contenu à la racine du dépôt, voici une séquence de commandes conseillée (vérifiez d'abord l'état du dépôt avec `git status`) :

```bash
# depuis le dossier racine du workspace
git mv pea-sim-parametric/* .
git mv pea-sim-parametric/.[!.]* .  # pour les fichiers cachés (attention aux shells Windows)
git commit -m "Move project files to repository root"
git rm -r pea-sim-parametric
git commit -m "Remove empty pea-sim-parametric folder"
```

Après cela, adaptez les chemins dans `pyproject.toml` / CI si nécessaire.

## Tests rapides

Pour exécuter la validation de base et les tests :

```bash
pea-sim validate --base configs/base.yaml --universe configs/universe.yaml --cost configs/cost_model.yaml --market configs/market_models/regimes.yaml --strategy configs/strategies/buy_and_hold_world.yaml
pytest -q
```

## Remarques

Ce MVP est un cadre d'analyse de scénarios : les résultats dépendent des paramètres choisis (drift, volatilité, corrélations, comportement des régimes). Ce n'est pas un backtest historique.
