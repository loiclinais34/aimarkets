# Système de Mise à Jour des Données Polygon.io

## 📋 Vue d'ensemble

Ce système permet de mettre à jour automatiquement les données historiques et de sentiment depuis l'API Polygon.io vers la base de données locale. Il inclut une logique intelligente pour identifier les données manquantes et gérer les décalages horaires entre la France et le marché Nasdaq.

## 🏗️ Architecture

### Backend

#### Services
- **`PolygonService`** (`app/services/polygon_service.py`): Interface avec l'API Polygon.io
- **`DataUpdateService`** (`app/services/data_update_service.py`): Logique de mise à jour des données

#### Endpoints API
- **`/api/v1/data-update/data-freshness`**: Statut de fraîcheur des données
- **`/api/v1/data-update/market-status`**: Statut du marché Nasdaq
- **`/api/v1/data-update/symbols-status`**: Statut de mise à jour par symbole
- **`/api/v1/data-update/update-historical/{symbol}`**: Mise à jour des données historiques
- **`/api/v1/data-update/update-sentiment/{symbol}`**: Mise à jour des données de sentiment
- **`/api/v1/data-update/update-all-data`**: Mise à jour complète de toutes les données

### Frontend

#### Composants
- **`DataFreshnessIndicator`** (`components/DataFreshnessIndicator.tsx`): Indicateur de fraîcheur des données
- **`dataUpdateApi`** (`services/api.ts`): Interface API pour la mise à jour des données

## 🔧 Fonctionnalités

### 1. Récupération des Données depuis Polygon.io

#### Données Historiques
- **Endpoint**: `https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{from_date}/{to_date}`
- **Données**: OHLCV + VWAP
- **Fréquence**: Quotidienne

#### Données de News
- **Endpoint**: `https://api.polygon.io/v2/reference/news`
- **Données**: Articles de news avec analyse de sentiment
- **Limite**: 1000 articles par requête

#### Données de Short Interest
- **Endpoint**: `https://api.polygon.io/stocks/v1/short-interest/{symbol}`
- **Données**: Ratio et volume de short interest

#### Données de Short Volume
- **Endpoint**: `https://api.polygon.io/stocks/v1/short-volume/{symbol}`
- **Données**: Volume de vente à découvert

### 2. Logique de Comparaison des Dates

Le système compare automatiquement :
- **Date en base de données** : Dernière date disponible localement
- **Date Polygon.io** : Dernière date disponible sur l'API
- **Dernier jour de trading** : Calculé selon le calendrier Nasdaq

**Critères de mise à jour** :
- Aucune donnée en base → Mise à jour nécessaire
- Données Polygon plus récentes → Mise à jour nécessaire
- Données antérieures au dernier jour de trading → Mise à jour nécessaire

### 3. Gestion des Fuseaux Horaires

#### Marché Nasdaq
- **Fuseau horaire** : America/New_York (EST/EDT)
- **Heures d'ouverture** : 9h30 - 16h00 (EST)
- **Jours fermés** : Weekends + jours fériés américains

#### Serveur (France)
- **Fuseau horaire** : Europe/Paris (CET/CEST)
- **Décalage** : +6h en hiver, +5h en été par rapport à EST

### 4. Indicateur de Fraîcheur des Données

L'indicateur affiche :
- **Statut global** : À jour / Mise à jour nécessaire / Erreur
- **Données historiques** : Dernière date + retard en jours
- **Données de sentiment** : Dernière date + retard en jours
- **Statut du marché** : Ouvert / Fermé
- **Bouton de mise à jour** : Déclenche la mise à jour des données

## 🚀 Utilisation

### 1. Configuration

#### Variables d'environnement
```bash
# Clé API Polygon.io
POLYGON_API_KEY=HVxEJr0Up37u0LNBN24tqb23qGKHW6Qt

# URL de l'API
POLYGON_BASE_URL=https://api.polygon.io
```

### 2. Démarrage

#### Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm run dev
```

### 3. Tests

#### Script de test complet
```bash
cd backend
python test_data_update_system.py
```

#### Tests individuels
```python
# Test du service Polygon
from app.services.polygon_service import PolygonService
polygon = PolygonService()
data = polygon.get_historical_data("AAPL", "2024-01-01", "2024-01-05")

# Test du service de mise à jour
from app.services.data_update_service import DataUpdateService
from app.core.database import get_db
db = next(get_db())
service = DataUpdateService(db)
result = service.update_historical_data_for_symbol("AAPL")
```

### 4. Endpoints API

#### Vérifier le statut des données
```bash
curl http://localhost:8000/api/v1/data-update/data-freshness
```

#### Mettre à jour un symbole spécifique
```bash
curl -X POST http://localhost:8000/api/v1/data-update/update-historical/AAPL
```

#### Mettre à jour toutes les données
```bash
curl -X POST http://localhost:8000/api/v1/data-update/update-all-data
```

## 📊 Schéma des Données

### Table `historical_data`
```sql
CREATE TABLE historical_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(10,4) NOT NULL,
    high DECIMAL(10,4) NOT NULL,
    low DECIMAL(10,4) NOT NULL,
    close DECIMAL(10,4) NOT NULL,
    volume BIGINT NOT NULL,
    vwap DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Table `sentiment_data`
```sql
CREATE TABLE sentiment_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    news_count INTEGER DEFAULT 0,
    news_sentiment_score DECIMAL(5,4) DEFAULT 0.0,
    news_sentiment_std DECIMAL(5,4) DEFAULT 0.0,
    news_positive_count INTEGER DEFAULT 0,
    news_negative_count INTEGER DEFAULT 0,
    news_neutral_count INTEGER DEFAULT 0,
    top_news_title TEXT,
    top_news_sentiment DECIMAL(5,4),
    top_news_url TEXT,
    short_interest_ratio DECIMAL(10,4),
    short_interest_volume BIGINT,
    short_interest_date DATE,
    short_volume BIGINT,
    short_exempt_volume BIGINT,
    total_volume BIGINT,
    short_volume_ratio DECIMAL(5,4),
    -- ... autres champs de sentiment
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 🔍 Monitoring et Logs

### Logs du Backend
```bash
# Activer les logs détaillés
export LOG_LEVEL=DEBUG
python -m uvicorn app.main:app --reload --log-level debug
```

### Logs du Frontend
```bash
# Logs dans la console du navigateur
# Ou logs du serveur de développement Next.js
npm run dev
```

## ⚠️ Limitations et Considérations

### Rate Limiting
- **Polygon.io** : Limite de requêtes par minute
- **Solution** : Délai de 100ms entre les requêtes
- **Recommandation** : Utiliser les tâches en arrière-plan pour les gros volumes

### Gestion des Erreurs
- **Erreurs réseau** : Retry automatique (3 tentatives)
- **Erreurs de données** : Logging et continuation du processus
- **Erreurs de base de données** : Rollback automatique

### Performance
- **Mise à jour en batch** : Traitement par lots pour éviter les timeouts
- **Tâches en arrière-plan** : Utilisation de BackgroundTasks pour les gros volumes
- **Cache** : Mise en cache des statuts pour réduire les requêtes

## 🛠️ Maintenance

### Mise à jour régulière
```bash
# Script de mise à jour quotidienne (cron)
0 18 * * 1-5 /path/to/update_daily.sh
```

### Vérification de l'intégrité
```bash
# Vérifier les données manquantes
python -c "
from app.services.data_update_service import DataUpdateService
from app.core.database import get_db
db = next(get_db())
service = DataUpdateService(db)
status = service.get_data_freshness_status()
print(f'Statut: {status[\"overall_status\"]}')
"
```

### Nettoyage des données
```sql
-- Supprimer les données anciennes (> 2 ans)
DELETE FROM historical_data WHERE date < CURRENT_DATE - INTERVAL '2 years';
DELETE FROM sentiment_data WHERE date < CURRENT_DATE - INTERVAL '2 years';
```

## 📈 Évolutions Futures

### Fonctionnalités prévues
- [ ] Mise à jour automatique par cron
- [ ] Notifications en cas d'erreur
- [ ] Dashboard de monitoring
- [ ] Support de multiples sources de données
- [ ] Cache Redis pour améliorer les performances
- [ ] API GraphQL pour des requêtes plus flexibles

### Optimisations
- [ ] Parallélisation des requêtes API
- [ ] Compression des données historiques
- [ ] Indexation optimisée des requêtes
- [ ] Mise en cache des calculs de sentiment

## 🤝 Contribution

Pour contribuer au système de mise à jour des données :

1. **Fork** le repository
2. **Créer** une branche feature
3. **Implémenter** les modifications
4. **Tester** avec le script de test
5. **Soumettre** une Pull Request

## 📞 Support

Pour toute question ou problème :
- **Issues GitHub** : Créer une issue avec le label `data-update`
- **Logs** : Inclure les logs d'erreur dans les rapports
- **Tests** : Exécuter `test_data_update_system.py` avant de reporter un bug
