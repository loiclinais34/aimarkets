#!/bin/bash

# Script de démarrage automatique pour Celery
# S'assure toujours d'être dans le bon répertoire

# Définir le répertoire de travail
BACKEND_DIR="/Users/loiclinais/Documents/dev/aimarkets/backend"

# Vérifier que le répertoire existe
if [ ! -d "$BACKEND_DIR" ]; then
    echo "❌ Erreur: Le répertoire $BACKEND_DIR n'existe pas"
    exit 1
fi

# Changer vers le répertoire backend
cd "$BACKEND_DIR"

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "app/core/celery_app.py" ]; then
    echo "❌ Erreur: Impossible de trouver app/core/celery_app.py"
    echo "   Répertoire actuel: $(pwd)"
    exit 1
fi

echo "✅ Démarrage de Celery depuis: $(pwd)"

# Vérifier que Redis est en cours d'exécution
if ! pgrep -x "redis-server" > /dev/null; then
    echo "⚠️  Attention: Redis ne semble pas être en cours d'exécution"
    echo "   Démarrez Redis avec: brew services start redis"
fi

# Démarrer Celery
echo "🚀 Lancement du worker Celery..."
celery -A app.core.celery_app worker --loglevel=info --concurrency=1
