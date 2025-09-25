# Framework de Comparaison de Modèles ML pour le Trading

## 🎯 Vue d'ensemble

Ce framework fournit un système complet pour comparer différents modèles d'apprentissage automatique dans le contexte du trading financier. Il permet d'évaluer les performances de multiples modèles ML et de sélectionner automatiquement le meilleur selon différents critères.

## 🚀 Fonctionnalités

### Modèles Supportés
- **Random Forest** : Modèle d'ensemble robuste et interprétable
- **XGBoost** : Gradient boosting optimisé pour les performances
- **LightGBM** : Gradient boosting rapide et efficace
- **Neural Networks** : Réseaux de neurones multi-couches
- **Modèles personnalisés** : Possibilité d'ajouter vos propres modèles

### Métriques d'Évaluation
- **Métriques ML** : Accuracy, Precision, Recall, F1-Score, ROC-AUC
- **Métriques de Trading** : Sharpe Ratio, Max Drawdown, Total Return, Win Rate, Profit Factor
- **Métriques Temporelles** : Temps d'entraînement, Temps de prédiction

### Fonctionnalités Avancées
- **Validation croisée temporelle** : Évite le data leakage
- **Backtesting intégré** : Simulation de trading réaliste
- **Recommandations automatiques** : Suggestions de modèles basées sur les caractéristiques du symbole
- **Comparaison multi-symboles** : Analyse agrégée sur plusieurs actifs
- **Rapports détaillés** : Génération automatique de rapports de performance

## 📁 Structure du Code

```
backend/app/services/
├── model_comparison_framework.py    # Framework principal
├── model_comparison_service.py      # Service d'intégration
└── ...

backend/app/api/endpoints/
└── model_comparison.py             # Endpoints API

backend/
├── test_model_comparison_framework.py  # Script de test
├── install_model_comparison_deps.sh    # Script d'installation
└── ...
```

## 🛠️ Installation

### 1. Installer les dépendances

```bash
cd backend
chmod +x install_model_comparison_deps.sh
./install_model_comparison_deps.sh
```

### 2. Vérifier l'installation

```bash
python test_model_comparison_framework.py
```

## 🔧 Utilisation

### Utilisation via API

#### 1. Obtenir les modèles disponibles
```bash
curl -X GET "http://localhost:8000/api/v1/model-comparison/available-models"
```

#### 2. Comparer les modèles pour un symbole
```bash
curl -X POST "http://localhost:8000/api/v1/model-comparison/compare-single" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "models_to_test": ["RandomForest", "XGBoost"],
    "start_date": "2023-01-01",
    "end_date": "2023-12-31"
  }'
```

#### 3. Obtenir des recommandations
```bash
curl -X POST "http://localhost:8000/api/v1/model-comparison/recommendations" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL"}'
```

### Utilisation en Python

```python
from app.services.model_comparison_service import ModelComparisonService
from app.core.database import get_db

# Créer le service
db = next(get_db())
service = ModelComparisonService(db)

# Comparer les modèles pour un symbole
result = service.compare_models_for_symbol(
    symbol="AAPL",
    models_to_test=["RandomForest", "XGBoost", "LightGBM"]
)

# Obtenir le meilleur modèle
if result['success']:
    best_model = result['best_model']
    print(f"Meilleur modèle: {best_model['name']}")
    print(f"F1-Score: {best_model['metrics']['f1_score']:.3f}")
```

## 📊 Exemple de Résultats

### Rapport de Comparaison
```
================================================================================
RAPPORT DE COMPARAISON DE MODÈLES
================================================================================
Date: 2024-01-15 14:30:25
Nombre de modèles comparés: 4

RÉSULTATS DÉTAILLÉS:
--------------------------------------------------------------------------------
Modèle                Accuracy   F1-Score   Sharpe     Return    
--------------------------------------------------------------------------------
RandomForest          0.756      0.742      1.234      0.156      
XGBoost              0.789      0.801      1.456      0.189      
LightGBM             0.782      0.795      1.389      0.178      
NeuralNetwork         0.734      0.728      1.123      0.134      
--------------------------------------------------------------------------------

MEILLEURS MODÈLES PAR MÉTRIQUE:
----------------------------------------
Accuracy: XGBoost (0.789)
F1_score: XGBoost (0.801)
Sharpe: XGBoost (1.456)
Total_return: XGBoost (0.189)
```

## 🎛️ Configuration

### Paramètres des Modèles

#### Random Forest
```python
RandomForestModel(
    name='CustomRF',
    n_estimators=200,      # Nombre d'arbres
    max_depth=10,         # Profondeur maximale
    min_samples_split=5,  # Échantillons minimum pour diviser
    min_samples_leaf=2    # Échantillons minimum par feuille
)
```

#### XGBoost
```python
XGBoostModel(
    name='CustomXGB',
    n_estimators=200,        # Nombre d'estimateurs
    max_depth=8,             # Profondeur maximale
    learning_rate=0.05,      # Taux d'apprentissage
    subsample=0.8,          # Fraction d'échantillons
    colsample_bytree=0.8    # Fraction de features
)
```

### Personnalisation des Features

Le framework utilise automatiquement les données disponibles :
- **Données historiques** : Prix, volumes, OHLC
- **Indicateurs techniques** : SMA, EMA, RSI, MACD, Bollinger Bands, etc.
- **Indicateurs de sentiment** : Score de sentiment, momentum, volatilité, etc.

## 🔍 Débogage

### Logs
Le framework génère des logs détaillés pour le débogage :
```python
import logging
logging.basicConfig(level=logging.INFO)
```

### Tests
Exécutez les tests pour vérifier le bon fonctionnement :
```bash
python test_model_comparison_framework.py
```

### Vérification de la Santé
```bash
curl -X GET "http://localhost:8000/api/v1/model-comparison/health"
```

## 📈 Performance

### Optimisations
- **Parallélisation** : Utilisation de `n_jobs=-1` pour les modèles supportés
- **Mise en cache** : Sauvegarde automatique des résultats
- **Validation temporelle** : Évite le data leakage
- **Features engineering** : Calcul automatique des indicateurs

### Limitations
- **Mémoire** : Les gros datasets peuvent nécessiter plus de RAM
- **Temps** : L'entraînement peut prendre du temps sur de gros datasets
- **Dépendances** : XGBoost et LightGBM sont optionnels

## 🤝 Contribution

### Ajouter un Nouveau Modèle

1. Créer une classe héritant de `BaseModel`
2. Implémenter la méthode `_create_model()`
3. Ajouter le modèle au framework

```python
class CustomModel(BaseModel):
    def _create_model(self):
        return YourCustomClassifier(**self.parameters)

# Ajouter au framework
framework.add_model('CustomModel', CustomModel('CustomModel'))
```

### Améliorer les Métriques

Les métriques de trading peuvent être personnalisées en modifiant la méthode `_calculate_trading_metrics()`.

## 📚 Références

- [Scikit-learn Documentation](https://scikit-learn.org/)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [LightGBM Documentation](https://lightgbm.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 🐛 Support

Pour signaler des bugs ou demander des fonctionnalités :
1. Vérifiez les logs pour les erreurs
2. Exécutez les tests pour identifier les problèmes
3. Consultez la documentation des dépendances

---

**Note** : Ce framework est conçu pour être extensible et modulaire. N'hésitez pas à l'adapter à vos besoins spécifiques !
