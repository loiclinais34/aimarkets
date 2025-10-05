from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn

from .core.config import settings
from .core.database import init_db, close_db
from .api.endpoints.auth import auth, users
from .api.endpoints.portfolio import portfolios, positions
from .api.endpoints.analysis import advanced_analysis, technical_analysis, sentiment_analysis, market_indicators, bubble_detection
from .api.endpoints.search import screener, signals, advanced_signals
from .api.endpoints.ml import ml_models, ml_backtesting, model_comparison, async_model_comparison, backtesting
from .api.endpoints.data import data, data_update, financial_ratios, indicators, correlations
from .api.endpoints.management import symbol_metadata, target_parameters, trading_strategies, celery_management


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie de l'application"""
    # Startup
    print("🚀 Démarrage de l'application AIMarkets...")
    init_db()
    print("✅ Base de données initialisée")
    
    yield
    
    # Shutdown
    print("🛑 Arrêt de l'application AIMarkets...")
    close_db()
    print("✅ Connexions fermées")


# Création de l'application FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API d'analyse d'opportunités sur les marchés financiers",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de sécurité
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
)


# Routes principales
@app.get("/")
async def root():
    """Point d'entrée de l'API"""
    return {
        "message": "Bienvenue sur l'API AIMarkets",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs" if settings.debug else "Documentation non disponible en production"
    }


@app.get("/health")
async def health_check():
    """Vérification de l'état de l'API"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment
    }


# Inclusion des routes des endpoints
app.include_router(
    data.router,
    prefix="/api/v1",
    tags=["Données"]
)

app.include_router(
    target_parameters.router,
    prefix="/api/v1",
    tags=["Paramètres de Cible"]
)

app.include_router(
    ml_models.router,
    prefix="/api/v1",
    tags=["Modèles ML"]
)

app.include_router(
    symbol_metadata.router,
    prefix="/api/v1/symbol-metadata",
    tags=["Métadonnées des Symboles"]
)

# Import du router screener
from app.api.endpoints.search import screener

app.include_router(
    screener.router,
    prefix="/api/v1/screener",
    tags=["Screener"]
)

# Import du router data_update
from app.api.endpoints.data import data_update

app.include_router(
    data_update.router,
    prefix="/api/v1/data-update",
    tags=["Mise à jour des Données"]
)

# Import du router celery_management
from app.api.endpoints.management import celery_management

app.include_router(
    celery_management.router,
    prefix="/api/v1",
    tags=["Gestion de Celery"]
)

# Import du router financial_ratios
from app.api.endpoints.data import financial_ratios

app.include_router(
    financial_ratios.router,
    prefix="/api/v1",
    tags=["Ratios Financiers"]
)

# Import du router advanced_analysis
from app.api.endpoints.analysis import advanced_analysis

app.include_router(
    advanced_analysis.router,
    prefix="/api/v1/advanced-analysis",
    tags=["Analyse Avancée"]
)

# Endpoints d'analyse technique, sentiment et marché
app.include_router(
    technical_analysis.router,
    prefix="/api/v1/technical-analysis",
    tags=["Analyse Technique"]
)

app.include_router(
    sentiment_analysis.router,
    prefix="/api/v1/sentiment-analysis",
    tags=["Analyse de Sentiment"]
)

app.include_router(
    market_indicators.router,
    prefix="/api/v1/market-indicators",
    tags=["Indicateurs de Marché"]
)

# Import du router indicators_recalculation
from app.api.endpoints.data import indicators_recalculation

app.include_router(
    indicators_recalculation.router,
    prefix="/api/v1",
    tags=["Recalcul des Indicateurs"]
)

# Import du router backtesting
from app.api.endpoints.ml import backtesting

app.include_router(
    backtesting.router,
    prefix="/api/v1/backtesting",
    tags=["Backtesting"]
)

# Import du router trading_strategies
from app.api.endpoints.management import trading_strategies

app.include_router(
    trading_strategies.router,
    prefix="/api/v1/strategies",
    tags=["Stratégies de Trading"]
)

# Import du router model_comparison
from app.api.endpoints.ml import model_comparison

app.include_router(
    model_comparison.router,
    prefix="/api/v1/model-comparison",
    tags=["Comparaison de Modèles"]
)

# Import du router async_model_comparison
from app.api.endpoints.ml import async_model_comparison

app.include_router(
    async_model_comparison.router,
    prefix="/api/v1/model-comparison",
    tags=["Comparaison Asynchrone de Modèles"]
)

# Import du router ml_backtesting
from app.api.endpoints.ml import ml_backtesting

app.include_router(
    ml_backtesting.router,
    prefix="/api/v1",
    tags=["ML Backtesting"]
)

# Bubble Detection API
from app.api.endpoints.analysis import bubble_detection

app.include_router(
    bubble_detection.router,
    prefix="/api/v1/bubble-detection",
    tags=["Bubble Detection"]
)

# Authentication & User Management API
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentification"]
)

app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["Gestion des Utilisateurs"]
)

# Portfolio Management API
app.include_router(
    portfolios.router,
    prefix="/api/v1/portfolios",
    tags=["Gestion des Portefeuilles"]
)

app.include_router(
    positions.router,
    prefix="/api/v1/positions",
    tags=["Gestion des Positions"]
)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning"
    )
