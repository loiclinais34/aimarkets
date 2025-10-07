"""
Endpoint pour générer l'analyse agent d'un titre
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pydantic import BaseModel
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.database import get_db
from app.models.database import SentimentData, HistoricalData
from app.api.endpoints.auth.auth import get_current_user

router = APIRouter()


class AgentAnalysisRequest(BaseModel):
    """Requête pour obtenir l'analyse agent d'un titre"""
    symbol: str
    days_back: int = 7  # Nombre de jours d'historique à analyser


class AgentAnalysisResponse(BaseModel):
    """Réponse avec l'analyse agent complète"""
    symbol: str
    analysis_date: str
    summary: Dict[str, Any]
    sentiment_evolution: List[Dict[str, Any]]
    price_evolution: List[Dict[str, Any]]
    correlation_analysis: Dict[str, Any]
    key_insights: List[str]
    recommendations: List[str]
    executive_narrative: str


@router.post("/agent-analysis", response_model=AgentAnalysisResponse)
async def generate_agent_analysis(
    request: AgentAnalysisRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Génère une analyse agent complète pour un titre donné
    """
    try:
        symbol = request.symbol.upper()
        days_back = request.days_back
        
        # Date de début pour l'analyse
        start_date = datetime.now() - timedelta(days=days_back)
        
        # Récupérer les données de sentiment
        sentiment_data = db.query(SentimentData).filter(
            SentimentData.symbol == symbol,
            SentimentData.date >= start_date.date()
        ).order_by(SentimentData.date.desc()).all()
        
        # Récupérer les données de cours
        price_data = db.query(HistoricalData).filter(
            HistoricalData.symbol == symbol,
            HistoricalData.date >= start_date.date()
        ).order_by(HistoricalData.date.desc()).all()
        
        if not price_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucune donnée de cours trouvée pour {symbol}"
            )
        
        # Analyser l'évolution du sentiment
        sentiment_evolution = []
        for data in sentiment_data:
            sentiment_evolution.append({
                "date": str(data.date),
                "sentiment_score": float(data.news_sentiment_score),
                "news_count": data.news_count,
                "positive_count": data.news_positive_count,
                "negative_count": data.news_negative_count,
                "neutral_count": data.news_neutral_count,
                "top_news_title": data.top_news_title,
                "analysis": data.sentiment_reasoning
            })
        
        # Analyser l'évolution des cours
        price_evolution = []
        for data in price_data:
            price_evolution.append({
                "date": str(data.date),
                "open": float(data.open),
                "close": float(data.close),
                "high": float(data.high),
                "low": float(data.low),
                "volume": data.volume
            })
        
        # Calculer les statistiques de performance
        if len(price_evolution) >= 2:
            latest_price = price_evolution[0]["close"]
            oldest_price = price_evolution[-1]["close"]
            price_change = latest_price - oldest_price
            price_change_pct = (price_change / oldest_price) * 100 if oldest_price > 0 else 0
        else:
            latest_price = price_evolution[0]["close"] if price_evolution else 0
            price_change = 0
            price_change_pct = 0
        
        # Analyser la corrélation sentiment/cours
        correlation_analysis = analyze_sentiment_price_correlation(sentiment_evolution, price_evolution)
        
        # Générer les insights clés
        key_insights = generate_key_insights(symbol, sentiment_evolution, price_evolution, correlation_analysis)
        
        # Générer les recommandations
        recommendations = generate_recommendations(symbol, sentiment_evolution, price_evolution, correlation_analysis)
        
        # Résumé exécutif amélioré
        summary = generate_executive_summary(symbol, sentiment_evolution, price_evolution, correlation_analysis, days_back)
        
        return AgentAnalysisResponse(
            symbol=symbol,
            analysis_date=datetime.now().isoformat(),
            summary=summary,
            sentiment_evolution=sentiment_evolution,
            price_evolution=price_evolution,
            correlation_analysis=correlation_analysis,
            key_insights=key_insights,
            recommendations=recommendations,
            executive_narrative=summary.get("executive_narrative", "")
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération de l'analyse: {str(e)}"
        )


def analyze_sentiment_price_correlation(sentiment_data: List[Dict], price_data: List[Dict]) -> Dict[str, Any]:
    """Analyse la corrélation entre sentiment et cours"""
    if not sentiment_data or not price_data:
        return {"correlation": "insuffisante", "sentiment_trend": "neutre", "news_impact": "limité"}
    
    # Calculer la moyenne du sentiment
    sentiment_scores = [s["sentiment_score"] for s in sentiment_data if s["sentiment_score"] != 0]
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
    
    # Déterminer la tendance du sentiment
    if avg_sentiment > 0.3:
        sentiment_trend = "positif"
    elif avg_sentiment < -0.3:
        sentiment_trend = "négatif"
    else:
        sentiment_trend = "neutre"
    
    # Analyser l'impact des news
    total_news = sum(s["news_count"] for s in sentiment_data)
    if total_news > 10:
        news_impact = "élevé"
    elif total_news > 5:
        news_impact = "modéré"
    else:
        news_impact = "limité"
    
    return {
        "correlation": "modérée" if sentiment_scores else "insuffisante",
        "sentiment_trend": sentiment_trend,
        "news_impact": news_impact,
        "average_sentiment": avg_sentiment,
        "total_news": total_news
    }


def generate_key_insights(symbol: str, sentiment_data: List[Dict], price_data: List[Dict], correlation: Dict) -> List[str]:
    """Génère les insights clés de l'analyse"""
    insights = []
    
    if price_data:
        latest_price = price_data[0]["close"]
        oldest_price = price_data[-1]["close"]
        change_pct = ((latest_price - oldest_price) / oldest_price) * 100 if oldest_price > 0 else 0
        
        insights.append(f"{symbol} a évolué de {change_pct:+.1f}% sur la période analysée")
    
    if sentiment_data:
        total_news = sum(s["news_count"] for s in sentiment_data)
        insights.append(f"{total_news} articles de news analysés sur la période")
        
        positive_news = sum(s["positive_count"] for s in sentiment_data)
        negative_news = sum(s["negative_count"] for s in sentiment_data)
        
        if positive_news > negative_news:
            insights.append(f"Sentiment globalement positif ({positive_news} positives vs {negative_news} négatives)")
        elif negative_news > positive_news:
            insights.append(f"Sentiment globalement négatif ({negative_news} négatives vs {positive_news} positives)")
        else:
            insights.append("Sentiment équilibré entre positif et négatif")
    
    # Analyser la volatilité
    if len(price_data) >= 2:
        prices = [p["close"] for p in price_data]
        volatility = calculate_volatility(price_data)
        if volatility > 0.05:
            insights.append(f"Volatilité élevée détectée ({volatility:.1%})")
        elif volatility < 0.02:
            insights.append(f"Volatilité faible ({volatility:.1%})")
    
    return insights


def generate_executive_summary(symbol: str, sentiment_data: List[Dict], price_data: List[Dict], correlation: Dict, days_back: int) -> Dict:
    """Génère un résumé exécutif humain et informatif"""
    if not price_data:
        return {
            "symbol": symbol,
            "analysis_period": f"{days_back} derniers jours",
            "current_price": 0,
            "price_change": 0,
            "price_change_pct": 0,
            "sentiment_trend": "neutre",
            "news_impact": "limité",
            "volatility": 0,
            "total_news_analyzed": 0,
            "executive_narrative": "Données insuffisantes pour générer une analyse complète."
        }
    
    latest_price = price_data[0]["close"]
    oldest_price = price_data[-1]["close"]
    price_change = latest_price - oldest_price
    price_change_pct = ((latest_price - oldest_price) / oldest_price) * 100 if oldest_price > 0 else 0
    
    # Calculs pour le récit
    total_news = sum(data["news_count"] for data in sentiment_data)
    positive_news = sum(data["positive_count"] for data in sentiment_data)
    negative_news = sum(data["negative_count"] for data in sentiment_data)
    volatility = calculate_volatility(price_data)
    
    # Génération du récit exécutif
    narrative_parts = []
    
    # Introduction contextuelle
    narrative_parts.append(f"Sur les {days_back} derniers jours, {symbol} a affiché une performance {'positive' if price_change_pct > 0 else 'négative' if price_change_pct < 0 else 'stable'}, avec une variation de {price_change_pct:+.2f}%.")
    
    # Analyse de la performance
    if abs(price_change_pct) > 10:
        narrative_parts.append(f"Cette évolution {'marquée' if price_change_pct > 0 else 'significative'} reflète une {'forte dynamique haussière' if price_change_pct > 0 else 'pression baissière importante'} sur la période.")
    elif abs(price_change_pct) > 5:
        narrative_parts.append(f"Cette performance {'solide' if price_change_pct > 0 else 'décevante'} indique une {'tendance constructive' if price_change_pct > 0 else 'faiblesse relative'} du titre.")
    else:
        narrative_parts.append("Cette évolution modérée suggère une phase de consolidation ou d'attente.")
    
    # Analyse du sentiment
    if total_news > 0:
        sentiment_ratio = positive_news / (positive_news + negative_news) if (positive_news + negative_news) > 0 else 0.5
        if sentiment_ratio > 0.7:
            narrative_parts.append(f"L'analyse de {total_news} articles de presse révèle un sentiment très positif ({positive_news} positives vs {negative_news} négatives), ce qui soutient la dynamique du titre.")
        elif sentiment_ratio > 0.6:
            narrative_parts.append(f"Le sentiment médiatique est favorable ({positive_news} positives vs {negative_news} négatives sur {total_news} articles), créant un environnement propice.")
        elif sentiment_ratio < 0.3:
            narrative_parts.append(f"Le sentiment est préoccupant ({negative_news} négatives vs {positive_news} positives sur {total_news} articles), ce qui pourrait peser sur les perspectives.")
        else:
            narrative_parts.append(f"Le sentiment médiatique est mitigé ({positive_news} positives vs {negative_news} négatives), reflétant une incertitude sur les perspectives.")
    
    # Analyse de la volatilité
    if volatility > 0.05:
        narrative_parts.append(f"La volatilité élevée ({volatility:.1%}) indique une période d'incertitude ou d'opportunités de trading importantes.")
    elif volatility < 0.02:
        narrative_parts.append(f"La faible volatilité ({volatility:.1%}) suggère une phase de stabilité relative, favorable aux investisseurs prudents.")
    else:
        narrative_parts.append(f"La volatilité modérée ({volatility:.1%}) offre un équilibre entre risque et opportunité.")
    
    # Conclusion contextuelle
    if price_change_pct > 5 and sentiment_ratio > 0.6:
        narrative_parts.append("Cette combinaison de performance positive et de sentiment favorable crée un environnement propice à une poursuite de la hausse.")
    elif price_change_pct < -5 and sentiment_ratio < 0.4:
        narrative_parts.append("La convergence entre performance décevante et sentiment négatif suggère une prudence accrue.")
    elif abs(price_change_pct) < 3 and volatility < 0.03:
        narrative_parts.append("Cette phase de stabilité pourrait être l'occasion d'accumuler en vue d'un mouvement directionnel futur.")
    else:
        narrative_parts.append("Les signaux mixtes nécessitent une surveillance attentive des prochaines évolutions.")
    
    executive_narrative = " ".join(narrative_parts)
    
    return {
        "symbol": symbol,
        "analysis_period": f"{days_back} derniers jours",
        "current_price": latest_price,
        "price_change": price_change,
        "price_change_pct": price_change_pct,
        "sentiment_trend": correlation.get("sentiment_trend", "neutre"),
        "news_impact": correlation.get("news_impact", "limité"),
        "volatility": volatility,
        "total_news_analyzed": total_news,
        "executive_narrative": executive_narrative
    }


def generate_recommendations(symbol: str, sentiment_data: List[Dict], price_data: List[Dict], correlation: Dict) -> List[str]:
    """Génère des recommandations basées sur l'analyse"""
    recommendations = []
    
    if not price_data:
        return ["Données insuffisantes pour générer des recommandations"]
    
    latest_price = price_data[0]["close"]
    oldest_price = price_data[-1]["close"]
    change_pct = ((latest_price - oldest_price) / oldest_price) * 100 if oldest_price > 0 else 0
    
    # Recommandations basées sur la performance
    if change_pct > 5:
        recommendations.append("Performance positive récente - Surveiller les niveaux de résistance")
    elif change_pct < -5:
        recommendations.append("Performance négative récente - Opportunité d'achat potentielle")
    else:
        recommendations.append("Performance stable - Attendre des signaux plus clairs")
    
    # Recommandations basées sur le sentiment
    sentiment_trend = correlation.get("sentiment_trend", "neutre")
    if sentiment_trend == "positif":
        recommendations.append("Sentiment positif - Favorable pour une position longue")
    elif sentiment_trend == "négatif":
        recommendations.append("Sentiment négatif - Prudence recommandée")
    else:
        recommendations.append("Sentiment neutre - Analyser d'autres facteurs techniques")
    
    # Recommandations basées sur l'impact des news
    news_impact = correlation.get("news_impact", "limité")
    if news_impact == "élevé":
        recommendations.append("Impact élevé des news - Surveiller les actualités régulièrement")
    elif news_impact == "modéré":
        recommendations.append("Impact modéré des news - Prendre en compte dans les décisions")
    
    return recommendations


def calculate_volatility(price_data: List[Dict]) -> float:
    """Calcule la volatilité des prix"""
    if len(price_data) < 2:
        return 0.0
    
    prices = [p["close"] for p in price_data]
    returns = []
    
    for i in range(1, len(prices)):
        if prices[i-1] > 0:
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(ret)
    
    if not returns:
        return 0.0
    
    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    volatility = variance ** 0.5
    
    return volatility
