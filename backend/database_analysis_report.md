# Analyse de la Base de Données - AIMarkets

## 📊 Vue d'ensemble

**Date d'analyse :** 27 septembre 2025  
**Total des tables :** 45 tables  
**Base de données :** PostgreSQL  

## 🎯 Tables Principales pour les Signaux Avancés

### 1. **Données Historiques de Cours** 📈

#### `historical_data` (69,109 enregistrements)
- **Colonnes clés :** `symbol`, `date`, `open`, `high`, `low`, `close`, `volume`, `vwap`
- **Période :** 2023-01-03 à 2025-09-26
- **Usage :** Base pour tous les calculs techniques et signaux
- **Top symboles :** ISRG, NXPI, CCEP, WBD, CSGP, META, PYPL, SHOP, AXON, FANG

### 2. **Données de Sentiment** 📰

#### `sentiment_data` (27,078 enregistrements)
- **Colonnes clés :** `symbol`, `date`, `news_sentiment_score`, `news_count`
- **Métriques :** Sentiment, momentum, volatilité, qualité des données
- **Usage :** Analyse de sentiment pour les signaux

#### `sentiment_indicators` (26,999 enregistrements)
- **Colonnes clés :** `symbol`, `date`, `sentiment_score_normalized`
- **Indicateurs :** Momentum, volatilité, moyennes mobiles, oscillateurs
- **Usage :** Indicateurs dérivés du sentiment

### 3. **Indicateurs Techniques** 🔧

#### `technical_indicators` (69,109 enregistrements)
- **Colonnes clés :** `symbol`, `date`
- **Indicateurs :** RSI, MACD, Bollinger Bands, moyennes mobiles, volume
- **Usage :** Base pour l'analyse technique et génération de signaux

### 4. **Signaux Avancés** 🎯

#### `advanced_signals` (11 enregistrements)
- **Colonnes clés :** `symbol`, `signal_type`, `score`, `confidence`, `strength`
- **Types de signaux :** STRONG_BUY, BUY, WEAK_BUY, HOLD, WEAK_SELL, SELL, STRONG_SELL
- **Symboles actifs :** AAPL (7 signaux), MSFT (2), GOOGL (2)
- **Usage :** Stockage des signaux générés par le système avancé

#### `signal_performance` (0 enregistrements)
- **Usage :** Suivi des performances des signaux (pas encore utilisé)

#### `signal_metrics` (0 enregistrements)
- **Usage :** Métriques agrégées des signaux (pas encore utilisé)

### 5. **Modèles ML** 🤖

#### `ml_models` (4,972 enregistrements)
- **Colonnes clés :** `symbol`, `model_name`, `model_type`, `performance_metrics`
- **Types :** RandomForest, XGBoost, LightGBM, Neural Network
- **Usage :** Modèles entraînés pour les prédictions

#### `ml_predictions` (288,844 enregistrements)
- **Colonnes clés :** `symbol`, `confidence`, `prediction_value`
- **Usage :** Prédictions des modèles ML

## 🔄 Flux de Données pour les Signaux

### 1. **Données d'Entrée**
```
historical_data → technical_indicators
sentiment_data → sentiment_indicators
ml_models → ml_predictions
```

### 2. **Génération de Signaux**
```
technical_indicators + sentiment_indicators + ml_predictions → advanced_signals
```

### 3. **Tables de Support**
- `symbol_metadata` : Métadonnées des symboles
- `search_sessions` : Sessions de recherche
- `screener_results` : Résultats du screener

## 📋 Tables par Catégorie

### **Données de Base (4 tables)**
- `historical_data` - Cours historiques
- `sentiment_data` - Données de sentiment
- `symbol_metadata` - Métadonnées
- `financial_ratios` - Ratios financiers

### **Indicateurs (4 tables)**
- `technical_indicators` - Indicateurs techniques
- `sentiment_indicators` - Indicateurs de sentiment
- `volatility_indicators` - Indicateurs de volatilité
- `momentum_indicators` - Indicateurs de momentum

### **Signaux (8 tables)**
- `advanced_signals` - Signaux avancés
- `technical_signals` - Signaux techniques
- `trading_signals` - Signaux de trading
- `signal_performance` - Performances des signaux
- `signal_metrics` - Métriques des signaux
- `signal_configurations` - Configurations
- `signal_backtests` - Backtests
- `candlestick_patterns` - Patterns de chandeliers

### **ML et Prédictions (2 tables)**
- `ml_models` - Modèles ML
- `ml_predictions` - Prédictions ML

### **Analyse Avancée (12 tables)**
- `garch_models` - Modèles GARCH
- `monte_carlo_simulations` - Simulations Monte Carlo
- `markov_chain_analysis` - Chaînes de Markov
- `volatility_forecasts` - Prédictions de volatilité
- `correlation_analysis` - Analyse de corrélation
- `market_indicators` - Indicateurs de marché
- `market_sentiment_summary` - Résumé de sentiment
- `support_resistance_levels` - Niveaux support/résistance
- `technical_analysis_summary` - Résumé technique
- `sentiment_analysis` - Analyse de sentiment
- `correlation_matrices` - Matrices de corrélation
- `cross_asset_correlations` - Corrélations croisées

### **Backtesting (4 tables)**
- `backtest_runs` - Exécutions de backtest
- `backtest_trades` - Trades de backtest
- `backtest_metrics` - Métriques de backtest
- `backtest_equity_curves` - Courbes de capital

### **Stratégies (4 tables)**
- `trading_strategies` - Stratégies de trading
- `strategy_rules` - Règles de stratégie
- `strategy_parameters` - Paramètres de stratégie
- `strategy_performance` - Performances de stratégie

### **Screener (4 tables)**
- `search_sessions` - Sessions de recherche
- `screener_configs` - Configurations du screener
- `screener_runs` - Exécutions du screener
- `screener_results` - Résultats du screener

### **Autres (3 tables)**
- `target_parameters` - Paramètres cibles
- `correlation_alerts` - Alertes de corrélation
- `correlation_features` - Features de corrélation

## 🎯 Recommandations

### **Tables Actives pour les Signaux**
1. **`historical_data`** - Données de base
2. **`technical_indicators`** - Indicateurs techniques
3. **`sentiment_indicators`** - Indicateurs de sentiment
4. **`ml_predictions`** - Prédictions ML
5. **`advanced_signals`** - Signaux générés

### **Tables à Développer**
1. **`signal_performance`** - Suivi des performances
2. **`signal_metrics`** - Métriques agrégées
3. **`signal_backtests`** - Backtesting des signaux

### **Optimisations Suggérées**
1. **Indexation :** `symbol`, `date` sur toutes les tables temporelles
2. **Partitionnement :** Par date pour les tables volumineuses
3. **Archivage :** Données anciennes (> 2 ans)
4. **Monitoring :** Taille des tables et performances des requêtes

## 📊 Métriques Clés

- **Volume total :** ~500,000 enregistrements
- **Symboles actifs :** 100+ symboles
- **Période couverte :** 2.5 ans (2023-2025)
- **Signaux générés :** 11 signaux avancés
- **Modèles ML :** 4,972 modèles entraînés
- **Prédictions :** 288,844 prédictions

## 🔧 Infrastructure Technique

- **Base de données :** PostgreSQL
- **ORM :** SQLAlchemy
- **Schéma :** `public`
- **Index :** Sur `symbol`, `date`, `signal_type`, `confidence`
- **Contraintes :** Clés étrangères et contraintes d'unicité
- **JSON :** Stockage de données complexes (paramètres, métriques)

---

*Rapport généré automatiquement le 27 septembre 2025*
