# Architecture du Framework de Comparaison de Modèles

## 🏗️ Vue d'ensemble de l'Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FRAMEWORK DE COMPARAISON DE MODÈLES                    │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FRONTEND       │    │     BACKEND      │    │    DATABASE      │
│   (Next.js)      │    │    (FastAPI)     │    │  (PostgreSQL)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Interface     │    │   API Endpoints │    │   Données       │
│   Utilisateur   │    │   /model-       │    │   Historiques   │
│                 │    │   comparison    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                    ┌─────────────────┐
                    │   Services      │
                    │   - Model       │
                    │     Comparison  │
                    │   - Data        │
                    │     Preparation │
                    └─────────────────┘
                                │
                                ▼
                    ┌─────────────────┐
                    │   Framework     │
                    │   Principal     │
                    │   - BaseModel   │
                    │   - Metrics     │
                    │   - Evaluation  │
                    └─────────────────┘
                                │
                                ▼
                    ┌─────────────────┐
                    │   Modèles ML    │
                    │   - Random       │
                    │     Forest       │
                    │   - XGBoost      │
                    │   - LightGBM     │
                    │   - Neural       │
                    │     Networks     │
                    └─────────────────┘
```

## 🔄 Flux de Données

```
1. RÉCUPÉRATION DES DONNÉES
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ Historical  │    │ Technical   │    │ Sentiment   │
   │ Data        │    │ Indicators  │    │ Indicators  │
   └─────────────┘    └─────────────┘    └─────────────┘
           │                   │                   │
           └───────────────────┼───────────────────┘
                               │
                               ▼
                    ┌─────────────────┐
                    │   DataFrame     │
                    │   Combiné       │
                    └─────────────────┘

2. PRÉPARATION DES FEATURES
   ┌─────────────────┐
   │   Features      │
   │   Engineering   │
   │   - Returns     │
   │   - Volumes     │
   │   - Volatilité  │
   │   - Ratios      │
   └─────────────────┘
           │
           ▼
   ┌─────────────────┐
   │   Features      │
   │   avec Lookback │
   │   (30 jours)    │
   └─────────────────┘

3. ENTRAÎNEMENT DES MODÈLES
   ┌─────────────────┐
   │   X_train       │
   │   y_train       │
   └─────────────────┘
           │
           ▼
   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
   │   Random        │    │   XGBoost        │    │   LightGBM      │
   │   Forest        │    │                  │    │                 │
   └─────────────────┘    └─────────────────┘    └─────────────────┘
           │                       │                       │
           └───────────────────────┼───────────────────────┘
                                   │
                                   ▼
                        ┌─────────────────┐
                        │   Modèles       │
                        │   Entraînés     │
                        └─────────────────┘

4. ÉVALUATION ET COMPARAISON
   ┌─────────────────┐
   │   X_test        │
   │   y_test        │
   │   prices_test   │
   └─────────────────┘
           │
           ▼
   ┌─────────────────┐    ┌─────────────────┐
   │   Métriques     │    │   Métriques     │
   │   ML            │    │   Trading       │
   │   - Accuracy    │    │   - Sharpe      │
   │   - F1-Score    │    │   - Drawdown    │
   │   - ROC-AUC     │    │   - Return      │
   └─────────────────┘    └─────────────────┘
           │                       │
           └───────────────────────┘
                       │
                       ▼
            ┌─────────────────┐
            │   Rapport de   │
            │   Comparaison   │
            │   - Meilleur    │
            │     Modèle      │
            │   - Rankings    │
            │   - Métriques   │
            └─────────────────┘
```

## 🧩 Composants Principaux

### 1. Framework Principal (`model_comparison_framework.py`)

```
BaseModel (Classe Abstraite)
├── RandomForestModel
├── XGBoostModel
├── LightGBMModel
└── NeuralNetworkModel

ModelComparisonFramework
├── compare_models()
├── get_best_model()
├── generate_report()
└── _save_results()
```

### 2. Service d'Intégration (`model_comparison_service.py`)

```
ModelComparisonService
├── prepare_training_data()
├── compare_models_for_symbol()
├── compare_models_for_multiple_symbols()
├── get_model_recommendations()
└── _analyze_symbol_characteristics()
```

### 3. Endpoints API (`model_comparison.py`)

```
/api/v1/model-comparison/
├── GET  /available-models
├── GET  /available-symbols
├── POST /compare-single
├── POST /compare-multiple
├── POST /recommendations
├── GET  /symbols/{symbol}/analysis
├── GET  /results
└── GET  /health
```

## 📊 Métriques d'Évaluation

### Métriques ML
- **Accuracy** : Précision globale des prédictions
- **Precision** : Précision des prédictions positives
- **Recall** : Sensibilité aux signaux d'achat
- **F1-Score** : Moyenne harmonique de precision et recall
- **ROC-AUC** : Aire sous la courbe ROC

### Métriques de Trading
- **Sharpe Ratio** : Rendement ajusté du risque
- **Max Drawdown** : Perte maximale depuis un pic
- **Total Return** : Rendement total sur la période
- **Win Rate** : Pourcentage de trades gagnants
- **Profit Factor** : Ratio profit brut / perte brute

### Métriques Temporelles
- **Training Time** : Temps d'entraînement du modèle
- **Prediction Time** : Temps de prédiction par échantillon

## 🔧 Configuration et Personnalisation

### Ajout d'un Nouveau Modèle

```python
class CustomModel(BaseModel):
    def _create_model(self):
        return YourCustomClassifier(**self.parameters)

# Ajouter au framework
framework.add_model('CustomModel', CustomModel('CustomModel'))
```

### Personnalisation des Features

```python
def _create_features_and_labels(self, df, lookback_days):
    # Ajouter vos propres features
    df['custom_feature'] = df['close'] / df['sma_20']
    
    # Modifier la logique des labels
    df['label'] = (df['future_return'] > 0.03).astype(int)  # 3% au lieu de 2%
```

### Personnalisation des Métriques

```python
def _calculate_trading_metrics(self, y_pred, y_pred_proba, prices):
    # Implémenter votre propre logique de trading
    # et calculer vos métriques personnalisées
    pass
```

## 🚀 Utilisation Avancée

### Comparaison Multi-Symboles

```python
# Comparer les modèles sur plusieurs symboles
result = service.compare_models_for_multiple_symbols(
    symbols=['AAPL', 'MSFT', 'GOOGL'],
    models_to_test=['RandomForest', 'XGBoost']
)

# Analyser les résultats agrégés
model_wins = result['model_wins']
avg_metrics = result['model_avg_metrics']
```

### Recommandations Automatiques

```python
# Obtenir des recommandations basées sur les caractéristiques
recommendations = service.get_model_recommendations('AAPL')

# Les recommandations sont basées sur:
# - Volatilité du symbole
# - Tendance du marché
# - Volume de trading
# - Caractéristiques techniques
```

### Sauvegarde et Chargement

```python
# Les résultats sont automatiquement sauvegardés
# dans model_comparison_results/model_comparison_TIMESTAMP.json

# Charger les résultats précédents
with open('model_comparison_results/latest.json', 'r') as f:
    results = json.load(f)
```

## 🔍 Débogage et Monitoring

### Logs Détaillés

```python
import logging
logging.basicConfig(level=logging.INFO)

# Les logs incluent:
# - Progression de l'entraînement
# - Métriques en temps réel
# - Erreurs et warnings
# - Temps d'exécution
```

### Tests Automatisés

```bash
# Exécuter tous les tests
python test_model_comparison_framework.py

# Tests inclus:
# - Données synthétiques
# - Création de modèles
# - Métriques de performance
# - Données réelles
```

### Health Check

```bash
# Vérifier l'état du service
curl -X GET "http://localhost:8000/api/v1/model-comparison/health"
```

## 📈 Optimisations et Performance

### Parallélisation

```python
# Les modèles utilisent automatiquement tous les cœurs disponibles
RandomForestModel(n_jobs=-1)
XGBoostModel(n_jobs=-1)
LightGBMModel(n_jobs=-1)
```

### Mise en Cache

```python
# Les résultats sont automatiquement sauvegardés
# Évite de recalculer les mêmes comparaisons
```

### Validation Temporelle

```python
# Utilise TimeSeriesSplit pour éviter le data leakage
# Respecte l'ordre chronologique des données
```

## 🔮 Extensions Futures

### Modèles Avancés
- **LSTM/GRU** : Pour les séries temporelles
- **Transformer** : Pour l'attention multi-assets
- **Reinforcement Learning** : Pour l'optimisation de stratégies

### Méthodes d'Ensemble
- **Stacking** : Meta-learner pour combiner les prédictions
- **Voting** : Vote majoritaire ou pondéré
- **Blending** : Combinaison des probabilités

### Optimisation Automatique
- **Hyperparameter Tuning** : Grid Search, Random Search, Bayesian
- **Feature Selection** : Sélection automatique des meilleures features
- **Model Selection** : Sélection automatique du meilleur modèle

### Persistance des Modèles
- **Sauvegarde** : Sauvegarder les modèles entraînés
- **Chargement** : Charger des modèles pré-entraînés
- **Versioning** : Gestion des versions de modèles

---

Cette architecture modulaire et extensible permet d'ajouter facilement de nouveaux modèles, métriques et fonctionnalités au framework de comparaison.
