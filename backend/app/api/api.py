from fastapi import APIRouter
from app.api.endpoints import authentication, wallets, portfolios, advanced_analysis
from app.api.endpoints.analysis import opportunity_performance, sophisticated_ml, technical_analysis, xgboost_opportunities, xgboost_performance

api_router = APIRouter()

api_router.include_router(
    authentication.router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    wallets.router,
    prefix="/wallets",
    tags=["wallets"]
)

api_router.include_router(
    portfolios.router,
    prefix="/portfolios",
    tags=["portfolios"]
)

api_router.include_router(
    advanced_analysis.router,
    prefix="/analysis/opportunities",
    tags=["opportunities"]
)

api_router.include_router(
    opportunity_performance.router,
    prefix="/analysis/opportunities",
    tags=["opportunities"]
)

api_router.include_router(
    sophisticated_ml.router,
    prefix="/analysis/sophisticated-ml",
    tags=["sophisticated-ml"]
)

api_router.include_router(
    technical_analysis.router,
    prefix="/technical-analysis",
    tags=["technical-analysis"]
)

api_router.include_router(
    xgboost_opportunities.router,
    prefix="/analysis",
    tags=["xgboost-opportunities"]
)

api_router.include_router(
    xgboost_performance.router,
    prefix="/analysis",
    tags=["xgboost-performance"]
)
