from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import redis
from .config import settings

# Configuration de la base de données
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections every hour
    echo=settings.debug
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()

# Métadonnées
metadata = MetaData()

# Configuration Redis
redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def get_db():
    """Dependency pour obtenir une session de base de données"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis():
    """Dependency pour obtenir le client Redis"""
    return redis_client


def init_db():
    """Initialiser la base de données"""
    # Créer toutes les tables
    Base.metadata.create_all(bind=engine)
    print("Base de données initialisée avec succès")


def close_db():
    """Fermer les connexions à la base de données"""
    engine.dispose()
    redis_client.close()
    print("Connexions à la base de données fermées")
