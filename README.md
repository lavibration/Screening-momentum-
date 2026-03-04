# Multivariate Factor Scoring Portfolio Tool

Cette application implémente une stratégie de sélection d'actions basée sur le papier de C. Reschenhofer (2023).

## Fonctionnalités
- **Scoring VIP** : Combine la Valeur (Book-to-Market), l'Investissement (Asset Growth) et la Profitabilité (Gross Profitability).
- **Filtre Momentum** : Exclut les actions ayant un momentum inférieur au 50ème percentile.
- **Zone de non-échange** : Réduit le turnover en maintenant les positions tant qu'elles ne tombent pas sous des seuils critiques.
- **Dashboard Interactif** : Visualisez les signaux Buy/Hold/Sell et la répartition sectorielle.

## Installation
```bash
pip install -r requirements.txt
```

## Utilisation
Pour lancer l'application Dash :
```bash
python src/app.py
```
L'interface sera disponible sur `http://127.0.0.1:8050`.

## Tests
Pour lancer les tests unitaires :
```bash
PYTHONPATH=. pytest tests/test_logic.py
```
