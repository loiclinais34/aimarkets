#!/bin/bash

# ===========================================
# Script de configuration AIMarkets
# ===========================================
# Ce script configure l'environnement et initialise la base de données

set -e  # Arrêter en cas d'erreur

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
print_message() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier si Docker est installé
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker n'est pas installé. Veuillez l'installer d'abord."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose n'est pas installé. Veuillez l'installer d'abord."
        exit 1
    fi
    
    print_success "Docker et Docker Compose sont installés"
}

# Créer le fichier .env s'il n'existe pas
create_env_file() {
    if [ ! -f .env ]; then
        print_message "Création du fichier .env..."
        cp env.example .env
        print_success "Fichier .env créé. Veuillez le modifier selon vos besoins."
        print_warning "IMPORTANT: Modifiez les mots de passe dans le fichier .env avant de continuer!"
        read -p "Appuyez sur Entrée une fois que vous avez modifié le fichier .env..."
    else
        print_success "Fichier .env existe déjà"
    fi
}

# Démarrer les services Docker
start_services() {
    print_message "Démarrage des services Docker..."
    docker-compose up -d postgres redis
    print_success "Services PostgreSQL et Redis démarrés"
    
    # Attendre que PostgreSQL soit prêt
    print_message "Attente que PostgreSQL soit prêt..."
    sleep 10
    
    # Vérifier la connexion à PostgreSQL
    if docker-compose exec -T postgres pg_isready -U aimarkets_user -d aimarkets; then
        print_success "PostgreSQL est prêt"
    else
        print_error "PostgreSQL n'est pas accessible"
        exit 1
    fi
}

# Initialiser la base de données
init_database() {
    print_message "Initialisation de la base de données..."
    
    # Créer la base de données
    docker-compose exec -T postgres psql -U aimarkets_user -d postgres -c "CREATE DATABASE IF NOT EXISTS aimarkets;" || true
    
    # Exécuter le script d'initialisation
    docker-compose exec -T postgres psql -U aimarkets_user -d aimarkets -f /docker-entrypoint-initdb.d/init.sql
    
    print_success "Base de données initialisée"
}

# Ingérer les données
ingest_data() {
    print_message "Ingestion des données..."
    
    # Copier les fichiers de données dans le conteneur
    docker cp historical_data.csv aimarkets_backend:/app/data/
    docker cp historcial_sentiment.csv aimarkets_backend:/app/data/
    
    # Exécuter le script d'ingestion
    docker-compose exec backend python scripts/data_ingestion.py ingest-all
    
    print_success "Données ingérées"
}

# Démarrer l'application complète
start_application() {
    print_message "Démarrage de l'application complète..."
    docker-compose up -d
    print_success "Application démarrée"
}

# Afficher les informations de connexion
show_connection_info() {
    echo ""
    echo "==========================================="
    echo "🎉 AIMarkets est maintenant configuré !"
    echo "==========================================="
    echo ""
    echo "📊 Accès aux services:"
    echo "  - Frontend: http://localhost:3000"
    echo "  - Backend API: http://localhost:8000"
    echo "  - Documentation API: http://localhost:8000/docs"
    echo "  - PostgreSQL: localhost:5432"
    echo "  - Redis: localhost:6379"
    echo ""
    echo "🔧 Commandes utiles:"
    echo "  - Voir les logs: docker-compose logs -f"
    echo "  - Arrêter: docker-compose down"
    echo "  - Redémarrer: docker-compose restart"
    echo ""
    echo "📚 Documentation:"
    echo "  - README.md pour plus d'informations"
    echo "  - PROJECT_PLAN.md pour le plan de développement"
    echo ""
}

# Fonction principale
main() {
    echo "==========================================="
    echo "🚀 Configuration AIMarkets"
    echo "==========================================="
    echo ""
    
    # Vérifications préalables
    check_docker
    
    # Configuration
    create_env_file
    
    # Démarrage des services
    start_services
    
    # Initialisation de la base de données
    init_database
    
    # Ingestion des données
    ingest_data
    
    # Démarrage de l'application
    start_application
    
    # Informations finales
    show_connection_info
}

# Gestion des arguments
case "${1:-}" in
    "check")
        check_docker
        ;;
    "env")
        create_env_file
        ;;
    "start")
        start_services
        ;;
    "init-db")
        init_database
        ;;
    "ingest")
        ingest_data
        ;;
    "full")
        main
        ;;
    *)
        echo "Usage: $0 {check|env|start|init-db|ingest|full}"
        echo ""
        echo "Commandes:"
        echo "  check     - Vérifier les prérequis"
        echo "  env       - Créer le fichier .env"
        echo "  start     - Démarrer les services de base"
        echo "  init-db   - Initialiser la base de données"
        echo "  ingest    - Ingérer les données"
        echo "  full      - Configuration complète (recommandé)"
        echo ""
        exit 1
        ;;
esac
