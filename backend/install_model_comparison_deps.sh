#!/bin/bash
# Script d'installation des dépendances pour le Framework de Comparaison de Modèles
# ================================================================================

echo "🔧 Installation des dépendances pour le Framework de Comparaison de Modèles"
echo "=========================================================================="

# Vérifier si nous sommes dans le bon répertoire
if [ ! -f "requirements.txt" ]; then
    echo "❌ Erreur: requirements.txt non trouvé. Exécutez ce script depuis le répertoire backend/"
    exit 1
fi

# Activer l'environnement virtuel si il existe
if [ -d "venv" ]; then
    echo "📦 Activation de l'environnement virtuel..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "📦 Activation de l'environnement virtuel..."
    source .venv/bin/activate
else
    echo "⚠️ Aucun environnement virtuel trouvé. Installation dans l'environnement global."
fi

# Installer les dépendances de base
echo "📥 Installation des dépendances de base..."
pip install --upgrade pip

# Dépendances ML principales
echo "🤖 Installation des bibliothèques ML..."
pip install scikit-learn>=1.3.0
pip install numpy>=1.24.0
pip install pandas>=2.0.0

# Dépendances optionnelles pour les modèles avancés
echo "🚀 Installation des modèles avancés..."

# XGBoost
echo "  - XGBoost..."
pip install xgboost>=1.7.0

# LightGBM
echo "  - LightGBM..."
pip install lightgbm>=4.0.0

# Vérifier les installations
echo "🔍 Vérification des installations..."

python -c "
import sys
print('Python version:', sys.version)

try:
    import sklearn
    print('✅ scikit-learn:', sklearn.__version__)
except ImportError as e:
    print('❌ scikit-learn non installé:', e)

try:
    import numpy as np
    print('✅ numpy:', np.__version__)
except ImportError as e:
    print('❌ numpy non installé:', e)

try:
    import pandas as pd
    print('✅ pandas:', pd.__version__)
except ImportError as e:
    print('❌ pandas non installé:', e)

try:
    import xgboost as xgb
    print('✅ xgboost:', xgb.__version__)
except ImportError as e:
    print('❌ xgboost non installé:', e)

try:
    import lightgbm as lgb
    print('✅ lightgbm:', lgb.__version__)
except ImportError as e:
    print('❌ lightgbm non installé:', e)
"

echo ""
echo "🎯 Installation terminée !"
echo ""
echo "📋 Prochaines étapes:"
echo "1. Exécutez le test du framework: python test_model_comparison_framework.py"
echo "2. Démarrez le serveur backend: python -m app.main"
echo "3. Testez les endpoints API dans la documentation Swagger"
echo ""
echo "🔗 Endpoints disponibles:"
echo "  - GET /api/v1/model-comparison/available-models"
echo "  - GET /api/v1/model-comparison/available-symbols"
echo "  - POST /api/v1/model-comparison/compare-single"
echo "  - POST /api/v1/model-comparison/compare-multiple"
echo "  - POST /api/v1/model-comparison/recommendations"
echo "  - GET /api/v1/model-comparison/health"
