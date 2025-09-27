# Scripts de Recalcul (Recompute)

Ce dossier contient les scripts de recalcul pour tous les éléments de l'analyse avancée.

## Scripts Disponibles

### 1. `recompute_technical_indicators.py`
Recalcule les indicateurs techniques pour tous les symboles ou des symboles spécifiques.

**Utilisation :**
```bash
# Recalculer pour tous les symboles
python3 recompute_technical_indicators.py

# Recalculer pour des symboles spécifiques
python3 recompute_technical_indicators.py --symbols AAPL MSFT GOOGL

# Forcer le recalcul même si les indicateurs existent
python3 recompute_technical_indicators.py --force

# Mode verbose
python3 recompute_technical_indicators.py --verbose
```

**Options :**
- `--symbols`: Symboles spécifiques à traiter (par défaut: tous)
- `--force`: Forcer le recalcul même si les indicateurs existent
- `--verbose`: Activer les logs détaillés

### 2. `recompute_sentiment_indicators.py`
Recalcule les indicateurs de sentiment pour tous les symboles ou des symboles spécifiques.

**Utilisation :**
```bash
# Recalculer pour tous les symboles ayant des données de sentiment
python3 recompute_sentiment_indicators.py

# Recalculer pour des symboles spécifiques
python3 recompute_sentiment_indicators.py --symbols AAPL MSFT GOOGL

# Forcer le recalcul
python3 recompute_sentiment_indicators.py --force
```

**Options :**
- `--symbols`: Symboles spécifiques à traiter (par défaut: tous avec données de sentiment)
- `--force`: Forcer le recalcul même si les indicateurs existent
- `--verbose`: Activer les logs détaillés

### 3. `recompute_market_indicators.py`
Recalcule les indicateurs de marché pour tous les symboles ou des symboles spécifiques.

**Utilisation :**
```bash
# Recalculer pour tous les symboles
python3 recompute_market_indicators.py

# Recalculer pour des symboles spécifiques
python3 recompute_market_indicators.py --symbols AAPL MSFT GOOGL

# Forcer le recalcul
python3 recompute_market_indicators.py --force
```

**Options :**
- `--symbols`: Symboles spécifiques à traiter (par défaut: tous)
- `--force`: Forcer le recalcul même si les indicateurs existent
- `--verbose`: Activer les logs détaillés

**Indicateurs calculés :**
- Volatilité historique (20 jours)
- Momentum de prix (5 et 20 jours)
- Ratio de volume moyen
- RSI (14 jours)

### 4. `recompute_advanced_opportunities.py`
Recalcule les opportunités avancées pour tous les symboles ou des symboles spécifiques.

**Utilisation :**
```bash
# Recalculer pour tous les symboles
python3 recompute_advanced_opportunities.py

# Recalculer pour des symboles spécifiques
python3 recompute_advanced_opportunities.py --symbols AAPL MSFT GOOGL

# Forcer le recalcul
python3 recompute_advanced_opportunities.py --force

# Modifier l'horizon temporel
python3 recompute_advanced_opportunities.py --time-horizon 60

# Désactiver l'analyse ML
python3 recompute_advanced_opportunities.py --no-ml
```

**Options :**
- `--symbols`: Symboles spécifiques à traiter (par défaut: tous)
- `--force`: Forcer le recalcul même si les opportunités existent
- `--time-horizon`: Horizon temporel en jours (par défaut: 30)
- `--no-ml`: Désactiver l'analyse ML
- `--verbose`: Activer les logs détaillés

### 5. `recompute_all.py` (Script Principal)
Orchestre le recalcul de tous les éléments en séquence.

**Utilisation :**
```bash
# Recalcul complet pour tous les symboles
python3 recompute_all.py

# Recalcul complet pour des symboles spécifiques
python3 recompute_all.py --symbols AAPL MSFT GOOGL

# Forcer le recalcul complet
python3 recompute_all.py --force

# Ignorer certains composants
python3 recompute_all.py --skip-technical --skip-sentiment

# Recalcul avec paramètres personnalisés
python3 recompute_all.py --time-horizon 60 --no-ml --force
```

**Options :**
- `--symbols`: Symboles spécifiques à traiter (par défaut: tous)
- `--force`: Forcer le recalcul même si les données existent
- `--skip-technical`: Ignorer le recalcul des indicateurs techniques
- `--skip-sentiment`: Ignorer le recalcul des indicateurs de sentiment
- `--skip-market`: Ignorer le recalcul des indicateurs de marché
- `--skip-opportunities`: Ignorer le recalcul des opportunités avancées
- `--time-horizon`: Horizon temporel en jours pour les opportunités (par défaut: 30)
- `--no-ml`: Désactiver l'analyse ML dans les opportunités
- `--verbose`: Activer les logs détaillés

## Ordre de Recalcul Recommandé

1. **Indicateurs techniques** - Base pour les autres analyses
2. **Indicateurs de sentiment** - Dépend des données de sentiment
3. **Indicateurs de marché** - Dépend des données historiques
4. **Opportunités avancées** - Dépend de tous les indicateurs précédents

## Exemples d'Utilisation

### Recalcul complet pour tous les symboles
```bash
python3 recompute_all.py --force --verbose
```

### Recalcul pour des symboles spécifiques
```bash
python3 recompute_all.py --symbols AAPL MSFT GOOGL TSLA NVDA --force
```

### Recalcul partiel (seulement les indicateurs)
```bash
python3 recompute_all.py --skip-opportunities --force
```

### Recalcul des opportunités avec horizon étendu
```bash
python3 recompute_all.py --skip-technical --skip-sentiment --skip-market --time-horizon 90
```

## Logs et Monitoring

Tous les scripts génèrent des logs détaillés incluant :
- Nombre de symboles traités
- Nombre de succès/échecs
- Durée d'exécution
- Erreurs détaillées
- Statistiques de performance

## Gestion des Erreurs

Les scripts gèrent automatiquement :
- Les erreurs de base de données
- Les rollbacks en cas d'échec
- La fermeture propre des connexions
- Le reporting des erreurs par symbole

## Performance

- Les scripts utilisent des transactions pour optimiser les performances
- Le mode `--force` supprime les anciennes données avant le recalcul
- Les logs permettent de monitorer la progression
- Les erreurs n'interrompent pas le traitement des autres symboles
