# Scripts Directory

Ce répertoire contient tous les scripts utilitaires organisés par catégorie pour une meilleure maintenance.

## Structure des dossiers

### 📁 `tests/` (38 fichiers)
Scripts de test et de débogage :
- Tests unitaires et d'intégration
- Tests de performance
- Scripts de débogage
- Validation de fonctionnalités

### 📁 `analysis/` (14 fichiers)
Scripts d'analyse et d'optimisation :
- Analyse de performance
- Optimisation des seuils
- Implémentation de nouvelles fonctionnalités
- Analyse des opportunités de trading

### 📁 `utilities/` (19 fichiers)
Scripts utilitaires généraux :
- Gestion de base de données
- Calculs d'indicateurs
- Traitement des données
- Scripts de maintenance

### 📁 `migrations/` (8 fichiers)
Scripts de migration et de mise à jour :
- Création de tables
- Migration de données
- Mises à jour de schéma
- Nettoyage de données

### 📁 `data_processing/` (4 fichiers)
Scripts de traitement de données :
- Ingestion de données
- Vérification de qualité
- Analyse de corrélations
- Traitement des indicateurs

### 📁 `results/` (19 fichiers)
Fichiers de résultats et rapports :
- Analyses JSON
- Métriques de performance
- Résultats de tests
- Rapports d'optimisation

## Utilisation

### Tests
```bash
# Exécuter un test spécifique
python scripts/tests/test_bubble_detection.py

# Tests de performance
python scripts/tests/test_optimized_buy_signals_performance.py
```

### Analyse
```bash
# Analyser les opportunités
python scripts/analysis/analyze_buy_opportunities.py

# Optimiser les seuils
python scripts/analysis/optimize_scoring_thresholds.py
```

### Migration
```bash
# Créer de nouvelles tables
python scripts/migrations/create_portfolio_tables.py

# Migrer les données
python scripts/migrations/migrate_ml_models.py
```

### Traitement de données
```bash
# Vérifier la qualité des données
python scripts/data_processing/quality_check_indicators.py

# Analyser les corrélations
python scripts/data_processing/correlation_analysis.py
```

## Maintenance

- Les scripts de test doivent être maintenus à jour avec les nouvelles fonctionnalités
- Les résultats sont automatiquement sauvegardés dans `results/`
- Les migrations doivent être testées avant application en production
- Les analyses peuvent être re-exécutées pour générer de nouveaux résultats

## Notes

- Tous les scripts utilisent les imports relatifs depuis `backend/`
- Les fichiers JSON de résultats sont générés automatiquement
- Certains scripts nécessitent une connexion à la base de données
- Les tests peuvent être exécutés individuellement ou en batch
