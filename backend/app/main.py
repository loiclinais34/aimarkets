from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn

from .core.config import settings
from .core.database import init_db, close_db
from .api.endpoints import data, target_parameters, ml_models, lightgbm_models, lightgbm_test, symbol_metadata, backtesting, trading_strategies, model_comparison, async_model_comparison, financial_ratios, technical_analysis, sentiment_analysis, market_indicators, advanced_signals


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
from app.api.endpoints import screener

app.include_router(
    screener.router,
    prefix="/api/v1/screener",
    tags=["Screener"]
)

# Import du router data_update
from app.api.endpoints import data_update

app.include_router(
    data_update.router,
    prefix="/api/v1/data-update",
    tags=["Mise à jour des Données"]
)

# Import du router celery_management
from app.api.endpoints import celery_management

app.include_router(
    celery_management.router,
    prefix="/api/v1",
    tags=["Gestion de Celery"]
)

# Import du router financial_ratios
from app.api.endpoints import financial_ratios

app.include_router(
    financial_ratios.router,
    prefix="/api/v1",
    tags=["Ratios Financiers"]
)

# Import du router indicators_recalculation
from app.api.endpoints import indicators_recalculation

app.include_router(
    indicators_recalculation.router,
    prefix="/api/v1",
    tags=["Recalcul des Indicateurs"]
)

# Import du router backtesting
from app.api.endpoints import backtesting

app.include_router(
    backtesting.router,
    prefix="/api/v1/backtesting",
    tags=["Backtesting"]
)

# Import du router trading_strategies
from app.api.endpoints import trading_strategies

app.include_router(
    trading_strategies.router,
    prefix="/api/v1/strategies",
    tags=["Stratégies de Trading"]
)

# Import du router model_comparison
from app.api.endpoints import model_comparison

app.include_router(
    model_comparison.router,
    prefix="/api/v1/model-comparison",
    tags=["Comparaison de Modèles"]
)

# Import du router async_model_comparison
from app.api.endpoints import async_model_comparison

app.include_router(
    async_model_comparison.router,
    prefix="/api/v1/model-comparison",
    tags=["Comparaison Asynchrone de Modèles"]
)

# Import du router technical_analysis
from app.api.endpoints import technical_analysis_simple

app.include_router(
    technical_analysis_simple.router,
    prefix="/api/v1/technical-analysis",
    tags=["Analyse Technique"]
)

# Import du router sentiment_analysis
from app.api.endpoints import sentiment_analysis

app.include_router(
    sentiment_analysis.router,
    prefix="/api/v1/sentiment-analysis",
    tags=["Analyse de Sentiment"]
)

# Import du router market_indicators
from app.api.endpoints import market_indicators

app.include_router(
    market_indicators.router,
    prefix="/api/v1/market-indicators",
    tags=["Indicateurs de Marché"]
)

# Import du router advanced_signals
from app.api.endpoints import advanced_signals

app.include_router(
    advanced_signals.router,
    prefix="/api/v1/advanced-signals",
    tags=["Signaux Avancés"]
)

# Import du router advanced_analysis
from app.api.endpoints import advanced_analysis

app.include_router(
    advanced_analysis.router,
    prefix="/api/v1",
    tags=["Analyse Avancée"]
)

# Endpoints LightGBM temporairement désactivés à cause de problèmes de stabilité
# app.include_router(
#     lightgbm_models.router,
#     prefix="/api/v1/lightgbm",
#     tags=["Modèles LightGBM"]
# )

# app.include_router(
#     lightgbm_test.router,
#     prefix="/api/v1/lightgbm-test",
#     tags=["LightGBM Test"]
# )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning"
    )
