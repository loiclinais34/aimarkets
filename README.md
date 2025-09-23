# AIMarkets - Application d'Analyse d'Opportunités Marchés Financiers

## 📋 Description

AIMarkets est une application d'analyse d'opportunités sur les marchés financiers qui combine l'analyse technique, le sentiment de marché et l'intelligence artificielle pour fournir des recommandations de trading avancées.

## 🏗️ Architecture

### Stack Technique
- **Backend** : Python FastAPI
- **Frontend** : Next.js/ReactJS avec TypeScript
- **Base de données** : PostgreSQL
- **Cache** : Redis
- **Containerisation** : Docker & Docker Compose

### Structure du Projet
```
aimarkets/
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── api/endpoints/   # Endpoints API
│   │   ├── core/           # Configuration et base de données
│   │   ├── models/         # Modèles de données
│   │   ├── services/       # Services métier
│   │   └── utils/          # Utilitaires
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # Interface Next.js
│   ├── src/
│   │   ├── components/     # Composants React
│   │   ├── pages/         # Pages Next.js
│   │   ├── services/      # Services API
│   │   ├── hooks/         # Hooks personnalisés
│   │   └── utils/         # Utilitaires
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml      # Configuration Docker
├── init.sql               # Script d'initialisation DB
└── README.md
```

## 🚀 Installation et Démarrage

### Prérequis
- Docker et Docker Compose
- Git

### Installation
1. **Cloner le repository**
   ```bash
   git clone <repository-url>
   cd aimarkets
   ```

2. **Démarrer les services**
   ```bash
   docker-compose up -d
   ```

3. **Vérifier le statut des services**
   ```bash
   docker-compose ps
   ```

### Accès aux Services
- **Frontend** : http://localhost:3000
- **Backend API** : http://localhost:8000
- **Documentation API** : http://localhost:8000/docs
- **PostgreSQL** : localhost:5432
- **Redis** : localhost:6379

## 📊 Données

### Fichiers de Données
- `historical_data.csv` : Données historiques des cours (100 titres NASDAQ, depuis 01/01/2023)
- `historical_sentiment.csv` : Données de sentiment de marché (depuis 01/01/2023)

### Structure des Données
- **Données historiques** : OHLCV + VWAP
- **Données de sentiment** : News sentiment, short interest, métriques dérivées

## 🔧 Configuration

### Variables d'Environnement
Créer un fichier `.env` à la racine du projet :
```env
# Base de données
DATABASE_URL=postgresql://aimarkets_user:aimarkets_password@localhost:5432/aimarkets

# Redis
REDIS_URL=redis://localhost:6379

# API
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
DEBUG=true

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📈 Fonctionnalités

### Phase 1 : Infrastructure ✅
- [x] Configuration PostgreSQL
- [x] Backend FastAPI
- [x] Frontend Next.js
- [x] Docker Compose

### Phase 2 : Traitement des Données
- [ ] Pipeline d'ingestion
- [ ] Indicateurs techniques
- [ ] Indicateurs de sentiment
- [ ] Calculs de corrélations

### Phase 3 : Machine Learning
- [ ] Préparation des données
- [ ] Modèles de classification
- [ ] Modèles de régression
- [ ] Modèles d'ensemble

### Phase 4 : Système de Recommandations
- [ ] Génération de signaux
- [ ] Gestion des risques
- [ ] Système d'alertes

### Phase 5 : Interface Utilisateur
- [ ] Dashboard principal
- [ ] Visualisations
- [ ] Configuration

## 🧪 Tests

### Backend
```bash
cd backend
python -m pytest
```

### Frontend
```bash
cd frontend
npm test
```

## 📚 API Documentation

### Endpoints Principaux
- `GET /api/v1/data/historical` - Données historiques
- `GET /api/v1/data/sentiment` - Données de sentiment
- `GET /api/v1/indicators/technical` - Indicateurs techniques
- `GET /api/v1/correlations/matrices` - Matrices de corrélation
- `GET /api/v1/signals/trading` - Signaux de trading
- `GET /api/v1/ml/models` - Modèles ML

### Documentation Interactive
Accéder à http://localhost:8000/docs pour la documentation interactive de l'API.

## 🔍 Développement

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Base de Données
```bash
# Connexion à PostgreSQL
docker exec -it aimarkets_postgres psql -U aimarkets_user -d aimarkets

# Connexion à Redis
docker exec -it aimarkets_redis redis-cli
```

## 📝 Logs

### Voir les logs
```bash
# Tous les services
docker-compose logs -f

# Service spécifique
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

## 🛠️ Maintenance

### Sauvegarde de la base de données
```bash
docker exec aimarkets_postgres pg_dump -U aimarkets_user aimarkets > backup.sql
```

### Restauration de la base de données
```bash
docker exec -i aimarkets_postgres psql -U aimarkets_user aimarkets < backup.sql
```

### Mise à jour des dépendances
```bash
# Backend
cd backend
pip install --upgrade -r requirements.txt

# Frontend
cd frontend
npm update
```

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📞 Support

Pour toute question ou problème, veuillez ouvrir une issue sur GitHub.

---

**AIMarkets** - Analyse d'opportunités sur les marchés financiers avec IA
