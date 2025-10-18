# Market Analysis Endpoints
from .opportunity_performance import router as opportunity_performance  # Import the router directly
from .advanced_analysis import router as advanced_analysis
from .technical_analysis import router as technical_analysis
from .sentiment_analysis import router as sentiment_analysis
from .market_indicators import router as market_indicators
from .bubble_detection import router as bubble_detection
from .sophisticated_ml import router as sophisticated_ml
from .ml_opportunities import router as ml_opportunities
from .ml_performance import router as ml_performance

__all__ = [
    "opportunity_performance",
    "advanced_analysis",
    "technical_analysis",
    "sentiment_analysis",
    "market_indicators",
    "bubble_detection",
    "sophisticated_ml",
    "ml_opportunities",
    "ml_performance"
]
