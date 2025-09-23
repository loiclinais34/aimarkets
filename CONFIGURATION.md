# Guide de Configuration AIMarkets

## 🔐 Configuration des Credentials

### 1. Fichier de Configuration

Le fichier `env.example` contient tous les paramètres de configuration nécessaires. Copiez-le vers `.env` et modifiez les valeurs selon vos besoins :

```bash
cp env.example .env
```

### 2. Variables d'Environnement Importantes

#### Base de Données PostgreSQL
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=aimarkets
DB_USER=aimarkets_user
DB_PASSWORD=aimarkets_password  # ⚠️ CHANGEZ CE MOT DE PASSE
```

#### Sécurité
```env
SECRET_KEY=your-super-secret-key-change-this-in-production  # ⚠️ CHANGEZ CETTE CLÉ
```

#### Redis
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # Optionnel pour le développement
```

## 🚀 Démarrage Rapide

### Option 1 : Configuration Automatique (Recommandé)

```bash
# Configuration complète automatique
./scripts/setup.sh full
```

### Option 2 : Configuration Manuelle

```bash
# 1. Créer le fichier .env
cp env.example .env
# Modifiez les mots de passe dans .env

# 2. Démarrer les services
docker-compose up -d postgres redis

# 3. Initialiser la base de données
docker-compose exec postgres psql -U aimarkets_user -d postgres -c "CREATE DATABASE aimarkets;"
docker-compose exec postgres psql -U aimarkets_user -d aimarkets -f /docker-entrypoint-initdb.d/init.sql

# 4. Ingérer les données
docker-compose exec backend python scripts/data_ingestion.py ingest-all

# 5. Démarrer l'application complète
docker-compose up -d
```

## 🔧 Gestion de la Base de Données

### Scripts Disponibles

#### Gestionnaire de Base de Données
```bash
# Vérifier la connexion
python backend/scripts/db_manager.py check

# Créer la base de données
python backend/scripts/db_manager.py create-db

# Créer les tables
python backend/scripts/db_manager.py create-tables

# Réinitialiser la base de données
python backend/scripts/db_manager.py reset

# Sauvegarder la base de données
python backend/scripts/db_manager.py backup --backup-path backup.sql

# Restaurer la base de données
python backend/scripts/db_manager.py restore --restore-path backup.sql

# Afficher les tables
python backend/scripts/db_manager.py tables

# Afficher les statistiques
python backend/scripts/db_manager.py stats
```

#### Script d'Ingestion des Données
```bash
# Ingérer les données historiques
python backend/scripts/data_ingestion.py ingest-historical --csv-path historical_data.csv

# Ingérer les données de sentiment
python backend/scripts/data_ingestion.py ingest-sentiment --csv-path historical_sentiment.csv

# Ingérer toutes les données
python backend/scripts/data_ingestion.py ingest-all

# Afficher les statistiques
python backend/scripts/data_ingestion.py stats
```

## 📊 Vérification de l'Installation

### 1. Vérifier les Services
```bash
# Statut des conteneurs
docker-compose ps

# Logs des services
docker-compose logs -f
```

### 2. Tester la Connexion à la Base de Données
```bash
# Connexion directe
docker-compose exec postgres psql -U aimarkets_user -d aimarkets

# Via le script
python backend/scripts/db_manager.py check
```

### 3. Tester l'API
```bash
# Santé de l'API
curl http://localhost:8000/health

# Documentation
open http://localhost:8000/docs
```

### 4. Tester le Frontend
```bash
# Accéder au frontend
open http://localhost:3000
```

## 🔒 Sécurité

### Mots de Passe Forts

Utilisez des mots de passe forts pour la production :

```env
# Exemple de configuration sécurisée
DB_PASSWORD=YourVeryStrongPassword123!
SECRET_KEY=your-very-long-random-secret-key-for-production
```

### Variables d'Environnement de Production

Pour la production, utilisez des variables d'environnement sécurisées :

```env
# Production
ENVIRONMENT=production
DEBUG=False
DB_SSL_MODE=require
REDIS_PASSWORD=your-redis-password
```

## 🐛 Dépannage

### Problèmes Courants

#### 1. Erreur de Connexion à la Base de Données
```bash
# Vérifier que PostgreSQL est démarré
docker-compose ps postgres

# Vérifier les logs
docker-compose logs postgres

# Redémarrer PostgreSQL
docker-compose restart postgres
```

#### 2. Erreur d'Ingestion des Données
```bash
# Vérifier que les fichiers CSV existent
ls -la *.csv

# Vérifier les permissions
chmod 644 *.csv

# Réessayer l'ingestion
python backend/scripts/data_ingestion.py ingest-all
```

#### 3. Erreur de Port Déjà Utilisé
```bash
# Vérifier les ports utilisés
netstat -tulpn | grep :5432
netstat -tulpn | grep :8000
netstat -tulpn | grep :3000

# Arrêter les services
docker-compose down

# Redémarrer
docker-compose up -d
```

### Logs et Debug

#### Activer les Logs Détaillés
```env
# Dans .env
DEBUG=True
LOG_LEVEL=DEBUG
```

#### Consulter les Logs
```bash
# Tous les services
docker-compose logs -f

# Service spécifique
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

## 📈 Monitoring

### Métriques de Base de Données
```bash
# Statistiques des tables
python backend/scripts/db_manager.py stats

# Taille de la base de données
docker-compose exec postgres psql -U aimarkets_user -d aimarkets -c "
SELECT pg_size_pretty(pg_database_size('aimarkets'));"
```

### Santé de l'Application
```bash
# Vérifier la santé de l'API
curl http://localhost:8000/health

# Vérifier les endpoints
curl http://localhost:8000/api/v1/data/stats
```

## 🔄 Maintenance

### Sauvegarde Régulière
```bash
# Sauvegarde automatique
python backend/scripts/db_manager.py backup --backup-path "backup_$(date +%Y%m%d_%H%M%S).sql"
```

### Mise à Jour
```bash
# Mettre à jour les images Docker
docker-compose pull

# Redémarrer avec les nouvelles images
docker-compose up -d
```

### Nettoyage
```bash
# Nettoyer les conteneurs arrêtés
docker-compose down
docker system prune -f

# Nettoyer les volumes (⚠️ Supprime les données)
docker-compose down -v
```

## 📞 Support

En cas de problème :

1. Consultez les logs : `docker-compose logs -f`
2. Vérifiez la configuration : `cat .env`
3. Testez la connexion : `python backend/scripts/db_manager.py check`
4. Consultez la documentation : `README.md`

---

**AIMarkets** - Configuration sécurisée et optimisée
