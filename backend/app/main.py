from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn

from .core.config import settings
from .core.database import init_db, close_db
from .api.endpoints.auth import auth, users
from .api.endpoints.portfolio import portfolios
from .api.endpoints import trading
from .api.endpoints import analysis as analysis_endpoints
from .api.endpoints import data as data_endpoints
from .api.endpoints import search as search_endpoints
from .api.endpoints import ml as ml_endpoints
from .api.endpoints import management as management_endpoints
from .api.endpoints.symbols import router as symbols_router
from .api.endpoints.management.target_parameters import router as target_parameters_router
from .api.endpoints.ml.ml_models import router as ml_models_router
from .api.endpoints.management.symbol_metadata import router as symbol_metadata_router


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
    data_endpoints.data,
    prefix="/api/v1",
    tags=["Données"]
)

from .api.endpoints.analysis.opportunity_performance import router as opportunity_performance_router
app.include_router(
    opportunity_performance_router,
    prefix="/api/v1/analysis/opportunities",
    tags=["Performance des Opportunités"]
)

from .api.endpoints.analysis.sophisticated_ml import router as sophisticated_ml_router
app.include_router(
    sophisticated_ml_router,
    prefix="/api/v1/analysis/sophisticated-ml",
    tags=["ML Sophistiqué"]
)

from .api.endpoints.analysis.ml_opportunities import router as ml_opportunities_router
app.include_router(
    ml_opportunities_router,
    prefix="/api/v1/analysis",
    tags=["ML Opportunities"]
)

from .api.endpoints.analysis.ml_test import router as ml_test_router
app.include_router(
    ml_test_router,
    prefix="/api/v1/analysis",
    tags=["ML Test"]
)

from .api.endpoints.analysis.ml_performance import router as ml_performance_router
app.include_router(
    ml_performance_router,
    prefix="/api/v1/analysis",
    tags=["ML Performance"]
)

app.include_router(
    target_parameters_router,
    prefix="/api/v1",
    tags=["Paramètres de Cible"]
)

app.include_router(
    ml_models_router,
    prefix="/api/v1",
    tags=["Modèles ML"]
)

app.include_router(
    symbol_metadata_router,
    prefix="/api/v1/symbol-metadata",
    tags=["Métadonnées des Symboles"]
)

# Import du router screener
from .api.endpoints.search.screener import router as screener_router

app.include_router(
    screener_router,
    prefix="/api/v1/screener",
    tags=["Screener"]
)

app.include_router(
    data_endpoints.data_update,
    prefix="/api/v1/data-update",
    tags=["Mise à jour des Données"]
)

from .api.endpoints.management.celery_management import router as celery_management_router
app.include_router(
    celery_management_router,
    prefix="/api/v1",
    tags=["Gestion de Celery"]
)

app.include_router(
    data_endpoints.financial_ratios,
    prefix="/api/v1",
    tags=["Ratios Financiers"]
)

# Endpoints d'analyse
app.include_router(
    analysis_endpoints.advanced_analysis,
    prefix="/api/v1/advanced-analysis",
    tags=["Analyse Avancée"]
)

app.include_router(
    analysis_endpoints.technical_analysis,
    prefix="/api/v1/technical-analysis",
    tags=["Analyse Technique"]
)

app.include_router(
    analysis_endpoints.sentiment_analysis,
    prefix="/api/v1/sentiment-analysis",
    tags=["Analyse de Sentiment"]
)

app.include_router(
    analysis_endpoints.market_indicators,
    prefix="/api/v1/market-indicators",
    tags=["Indicateurs de Marché"]
)

# Endpoints de données
app.include_router(
    data_endpoints.indicators_recalculation,
    prefix="/api/v1",
    tags=["Recalcul des Indicateurs"]
)

app.include_router(
    data_endpoints.realtime_prices,
    prefix="/api/v1",
    tags=["Cours en Temps Réel (Polygon)"]
)

from .api.endpoints.analysis.agent_analysis import router as agent_analysis_router
app.include_router(
    agent_analysis_router,
    prefix="/api/v1/analysis",
    tags=["Analyse Agent"]
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
app.include_router(
    analysis_endpoints.bubble_detection,
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
    trading.router,
    prefix="/api/v1/trading",
    tags=["Trading de Titres"]
)

# Symbols API
app.include_router(
    symbols_router,
    prefix="/api/v1",
    tags=["Symboles et Métadonnées"]
)

# Import du router latest_prices
from .api.endpoints.data.latest_prices import router as latest_prices_router

app.include_router(
    latest_prices_router,
    prefix="/api/v1",
    tags=["Cours en Temps Réel"]
)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning"
    )
