"""
Endpoints API pour le Framework de Comparaison de Modèles
=========================================================

Ce module expose les fonctionnalités du framework de comparaison
de modèles via des endpoints REST API.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...core.database import get_db
from ...services.model_comparison_service import ModelComparisonService

logger = logging.getLogger(__name__)

router = APIRouter()

# Modèles Pydantic pour les requêtes et réponses
class ModelComparisonRequest(BaseModel):
    """Requête pour comparer les modèles"""
    symbol: str = Field(..., description="Symbole à analyser")
    models_to_test: Optional[List[str]] = Field(None, description="Liste des modèles à tester")
    start_date: Optional[date] = Field(None, description="Date de début")
    end_date: Optional[date] = Field(None, description="Date de fin")

class MultiSymbolComparisonRequest(BaseModel):
    """Requête pour comparer les modèles sur plusieurs symboles"""
    symbols: List[str] = Field(..., description="Liste des symboles à analyser")
    models_to_test: Optional[List[str]] = Field(None, description="Liste des modèles à tester")

class ModelRecommendationRequest(BaseModel):
    """Requête pour obtenir des recommandations de modèles"""
    symbol: str = Field(..., description="Symbole à analyser")

@router.get("/available-models", response_model=Dict[str, Any])
def get_available_models():
    """Obtenir la liste des modèles disponibles"""
    try:
        available_models = {
            'RandomForest': {
                'name': 'Random Forest',
                'description': 'Modèle d\'ensemble robuste et interprétable',
                'type': 'ensemble',
                'parameters': {
                    'n_estimators': 'Nombre d\'arbres (défaut: 100)',
                    'max_depth': 'Profondeur maximale (défaut: None)',
                    'min_samples_split': 'Échantillons minimum pour diviser (défaut: 2)',
                    'min_samples_leaf': 'Échantillons minimum par feuille (défaut: 1)'
                }
            },
            'XGBoost': {
                'name': 'XGBoost',
                'description': 'Gradient boosting optimisé pour les performances',
                'type': 'gradient_boosting',
                'parameters': {
                    'n_estimators': 'Nombre d\'estimateurs (défaut: 100)',
                    'max_depth': 'Profondeur maximale (défaut: 6)',
                    'learning_rate': 'Taux d\'apprentissage (défaut: 0.1)',
                    'subsample': 'Fraction d\'échantillons (défaut: 1.0)',
                    'colsample_bytree': 'Fraction de features (défaut: 1.0)'
                }
            },
            'LightGBM': {
                'name': 'LightGBM',
                'description': 'Gradient boosting rapide et efficace',
                'type': 'gradient_boosting',
                'parameters': {
                    'n_estimators': 'Nombre d\'estimateurs (défaut: 100)',
                    'max_depth': 'Profondeur maximale (défaut: -1)',
                    'learning_rate': 'Taux d\'apprentissage (défaut: 0.1)',
                    'subsample': 'Fraction d\'échantillons (défaut: 1.0)',
                    'colsample_bytree': 'Fraction de features (défaut: 1.0)'
                }
            },
            'NeuralNetwork': {
                'name': 'Neural Network',
                'description': 'Réseau de neurones multi-couches',
                'type': 'neural_network',
                'parameters': {
                    'hidden_layer_sizes': 'Tailles des couches cachées (défaut: (100, 50))',
                    'activation': 'Fonction d\'activation (défaut: relu)',
                    'solver': 'Algorithme d\'optimisation (défaut: adam)',
                    'alpha': 'Paramètre de régularisation (défaut: 0.0001)',
                    'learning_rate': 'Taux d\'apprentissage (défaut: constant)',
                    'max_iter': 'Nombre maximum d\'itérations (défaut: 1000)'
                }
            }
        }
        
        return {
            'success': True,
            'available_models': available_models,
            'total': len(available_models)
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des modèles disponibles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des modèles: {str(e)}"
        )

@router.get("/available-symbols", response_model=Dict[str, Any])
def get_available_symbols(db: Session = Depends(get_db)):
    """Obtenir la liste des symboles disponibles pour la comparaison"""
    try:
        service = ModelComparisonService(db)
        symbols = service.get_available_symbols()
        
        return {
            'success': True,
            'symbols': symbols,
            'total': len(symbols)
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des symboles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des symboles: {str(e)}"
        )

@router.post("/compare-with-interpretations", response_model=Dict[str, Any])
def compare_models_with_interpretations(
    request: ModelComparisonRequest,
    db: Session = Depends(get_db)
):
    """
    Comparer les modèles avec des interprétations intelligentes et des recommandations
    
    Cette endpoint fournit une analyse complète avec:
    - Interprétations détaillées de chaque métrique
    - Recommandations spécifiques par modèle
    - Évaluation globale de la tradabilité
    - Alertes de risque
    """
    try:
        service = ModelComparisonService(db)
        
        # Effectuer la comparaison standard
        result = service.compare_models_for_symbol(
            symbol=request.symbol,
            models_to_test=request.models_to_test,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'Erreur lors de la comparaison')
            )
        
        # Enrichir avec les interprétations
        # Les résultats bruts sont dans result['results']
        enriched_results = service.analyze_results_with_interpretations(result['results'])
        
        return {
            "success": True,
            "symbol": request.symbol,
            "timestamp": datetime.now().isoformat(),
            "results": enriched_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la comparaison avec interprétations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la comparaison: {str(e)}"
        )

@router.post("/compare-single", response_model=Dict[str, Any])
def compare_models_single_symbol(
    request: ModelComparisonRequest,
    db: Session = Depends(get_db)
):
    """Comparer les modèles pour un symbole donné"""
    try:
        service = ModelComparisonService(db)
        
        result = service.compare_models_for_symbol(
            symbol=request.symbol,
            models_to_test=request.models_to_test,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'Erreur lors de la comparaison')
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la comparaison pour {request.symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la comparaison: {str(e)}"
        )

@router.post("/compare-multiple", response_model=Dict[str, Any])
def compare_models_multiple_symbols(
    request: MultiSymbolComparisonRequest,
    db: Session = Depends(get_db)
):
    """Comparer les modèles pour plusieurs symboles"""
    try:
        service = ModelComparisonService(db)
        
        result = service.compare_models_for_multiple_symbols(
            symbols=request.symbols,
            models_to_test=request.models_to_test
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Erreur lors de la comparaison multiple: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la comparaison multiple: {str(e)}"
        )

@router.post("/recommendations", response_model=Dict[str, Any])
def get_model_recommendations(
    request: ModelRecommendationRequest,
    db: Session = Depends(get_db)
):
    """Obtenir des recommandations de modèles pour un symbole"""
    try:
        service = ModelComparisonService(db)
        
        result = service.get_model_recommendations(request.symbol)
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'Erreur lors de l\'analyse')
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l\'analyse de {request.symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l\'analyse: {str(e)}"
        )

@router.get("/symbols/{symbol}/analysis", response_model=Dict[str, Any])
def analyze_symbol_characteristics(
    symbol: str,
    db: Session = Depends(get_db)
):
    """Analyser les caractéristiques d'un symbole"""
    try:
        service = ModelComparisonService(db)
        
        # Utiliser la méthode privée via une méthode publique
        analysis = service._analyze_symbol_characteristics(symbol)
        
        return {
            'success': True,
            'symbol': symbol,
            'analysis': analysis
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l\'analyse de {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l\'analyse: {str(e)}"
        )

@router.get("/results", response_model=Dict[str, Any])
def get_comparison_results(
    limit: int = Query(10, description="Nombre de résultats à retourner"),
    offset: int = Query(0, description="Décalage pour la pagination"),
    db: Session = Depends(get_db)
):
    """Obtenir les résultats de comparaison précédents"""
    try:
        # Pour l'instant, retourner un message indiquant que cette fonctionnalité
        # sera implémentée dans une version future
        return {
            'success': True,
            'message': 'Cette fonctionnalité sera implémentée dans une version future',
            'results': [],
            'total': 0,
            'limit': limit,
            'offset': offset
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des résultats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des résultats: {str(e)}"
        )

@router.get("/health", response_model=Dict[str, Any])
def health_check():
    """Vérifier la santé du service de comparaison de modèles"""
    try:
        return {
            'success': True,
            'service': 'Model Comparison Framework',
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du health check: {str(e)}"
        )
