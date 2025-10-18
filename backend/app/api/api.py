from fastapi import APIRouter
from app.api.endpoints import authentication, wallets, portfolios, advanced_analysis
from app.api.endpoints.analysis import opportunity_performance, sophisticated_ml

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
