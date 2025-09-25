"""
API Endpoints pour les Stratégies de Trading
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from ...core.database import get_db
from ...models.database import TradingStrategy, StrategyRule, StrategyParameter
from ...services.trading_strategy_service import TradingStrategyService
from ...services.predefined_strategies import PredefinedStrategies, StrategyInitializer

router = APIRouter()


# ==================== PYDANTIC MODELS ====================

class StrategyRuleCreate(BaseModel):
    rule_type: str = Field(..., description="Type de règle: entry, exit, position_sizing, risk_management")
    rule_name: str = Field(..., description="Nom de la règle")
    rule_condition: str = Field(..., description="Condition logique")
    rule_action: str = Field(..., description="Action à exécuter")
    priority: int = Field(1, description="Priorité d'exécution")


class StrategyCreate(BaseModel):
    name: str = Field(..., description="Nom de la stratégie")
    description: str = Field(..., description="Description de la stratégie")
    strategy_type: str = Field(..., description="Type de stratégie")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Paramètres de la stratégie")
    rules: List[StrategyRuleCreate] = Field(..., description="Règles de la stratégie")
    created_by: str = Field("user", description="Utilisateur créateur")


class StrategyUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Nom de la stratégie")
    description: Optional[str] = Field(None, description="Description de la stratégie")
    strategy_type: Optional[str] = Field(None, description="Type de stratégie")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Paramètres de la stratégie")
    is_active: Optional[bool] = Field(None, description="Statut actif")


class StrategyRuleUpdate(BaseModel):
    rule_type: Optional[str] = Field(None, description="Type de règle")
    rule_name: Optional[str] = Field(None, description="Nom de la règle")
    rule_condition: Optional[str] = Field(None, description="Condition logique")
    rule_action: Optional[str] = Field(None, description="Action à exécuter")
    priority: Optional[int] = Field(None, description="Priorité d'exécution")
    is_active: Optional[bool] = Field(None, description="Statut actif")


class StrategyResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    strategy_type: str
    parameters: Dict[str, Any]
    is_active: bool
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime]


class StrategyRuleResponse(BaseModel):
    id: int
    rule_type: str
    rule_name: str
    rule_condition: str
    rule_action: str
    priority: int
    is_active: bool


class StrategyDetailResponse(BaseModel):
    strategy: StrategyResponse
    rules: List[StrategyRuleResponse]


class MessageResponse(BaseModel):
    message: str
    success: bool = True


# ==================== API ENDPOINTS ====================

@router.post("/create", response_model=Dict[str, Any])
def create_strategy(
    strategy_data: StrategyCreate,
    db: Session = Depends(get_db)
):
    """Créer une nouvelle stratégie de trading"""
    try:
        strategy_service = TradingStrategyService(db)
        
        # Convertir les règles
        rules_data = [
            {
                "rule_type": rule.rule_type,
                "rule_name": rule.rule_name,
                "rule_condition": rule.rule_condition,
                "rule_action": rule.rule_action,
                "priority": rule.priority
            }
            for rule in strategy_data.rules
        ]
        
        result = strategy_service.create_strategy(
            name=strategy_data.name,
            description=strategy_data.description,
            strategy_type=strategy_data.strategy_type,
            parameters=strategy_data.parameters,
            rules=rules_data,
            created_by=strategy_data.created_by
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de la stratégie: {str(e)}"
        )


@router.get("/", response_model=Dict[str, Any])
def get_strategies(
    skip: int = 0,
    limit: int = 100,
    strategy_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Récupérer la liste des stratégies"""
    try:
        strategy_service = TradingStrategyService(db)
        
        result = strategy_service.get_strategies(
            skip=skip,
            limit=limit,
            strategy_type=strategy_type,
            is_active=is_active
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des stratégies: {str(e)}"
        )


@router.get("/{strategy_id}", response_model=Dict[str, Any])
def get_strategy(
    strategy_id: int,
    db: Session = Depends(get_db)
):
    """Récupérer une stratégie spécifique avec ses règles"""
    try:
        strategy_service = TradingStrategyService(db)
        
        result = strategy_service.get_strategy(strategy_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération de la stratégie: {str(e)}"
        )


@router.put("/{strategy_id}", response_model=Dict[str, Any])
def update_strategy(
    strategy_id: int,
    strategy_data: StrategyUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour une stratégie"""
    try:
        strategy_service = TradingStrategyService(db)
        
        result = strategy_service.update_strategy(
            strategy_id=strategy_id,
            name=strategy_data.name,
            description=strategy_data.description,
            strategy_type=strategy_data.strategy_type,
            parameters=strategy_data.parameters,
            is_active=strategy_data.is_active
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour de la stratégie: {str(e)}"
        )


@router.delete("/{strategy_id}", response_model=MessageResponse)
def delete_strategy(
    strategy_id: int,
    db: Session = Depends(get_db)
):
    """Supprimer une stratégie"""
    try:
        strategy_service = TradingStrategyService(db)
        
        result = strategy_service.delete_strategy(strategy_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return MessageResponse(
            message=result["message"],
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression de la stratégie: {str(e)}"
        )


@router.post("/{strategy_id}/rules", response_model=Dict[str, Any])
def add_strategy_rule(
    strategy_id: int,
    rule_data: StrategyRuleCreate,
    db: Session = Depends(get_db)
):
    """Ajouter une règle à une stratégie"""
    try:
        strategy_service = TradingStrategyService(db)
        
        result = strategy_service.add_strategy_rule(
            strategy_id=strategy_id,
            rule_type=rule_data.rule_type,
            rule_name=rule_data.rule_name,
            rule_condition=rule_data.rule_condition,
            rule_action=rule_data.rule_action,
            priority=rule_data.priority
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'ajout de la règle: {str(e)}"
        )


@router.put("/rules/{rule_id}", response_model=Dict[str, Any])
def update_strategy_rule(
    rule_id: int,
    rule_data: StrategyRuleUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour une règle de stratégie"""
    try:
        strategy_service = TradingStrategyService(db)
        
        result = strategy_service.update_strategy_rule(
            rule_id=rule_id,
            rule_type=rule_data.rule_type,
            rule_name=rule_data.rule_name,
            rule_condition=rule_data.rule_condition,
            rule_action=rule_data.rule_action,
            priority=rule_data.priority,
            is_active=rule_data.is_active
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour de la règle: {str(e)}"
        )


@router.delete("/rules/{rule_id}", response_model=MessageResponse)
def delete_strategy_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Supprimer une règle de stratégie"""
    try:
        strategy_service = TradingStrategyService(db)
        
        result = strategy_service.delete_strategy_rule(rule_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return MessageResponse(
            message=result["message"],
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression de la règle: {str(e)}"
        )


@router.get("/{strategy_id}/performance", response_model=Dict[str, Any])
def get_strategy_performance(
    strategy_id: int,
    db: Session = Depends(get_db)
):
    """Récupérer les performances d'une stratégie"""
    try:
        strategy_service = TradingStrategyService(db)
        
        result = strategy_service.get_strategy_performance(strategy_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des performances: {str(e)}"
        )


@router.get("/predefined/types", response_model=Dict[str, Any])
def get_predefined_strategy_types():
    """Récupérer les types de stratégies prédéfinies disponibles"""
    try:
        strategies = PredefinedStrategies.get_all_strategies()
        
        strategy_types = [
            {
                "type": strategy["strategy_type"],
                "name": strategy["name"],
                "description": strategy["description"]
            }
            for strategy in strategies
        ]
        
        return {
            "success": True,
            "strategy_types": strategy_types
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des types: {str(e)}"
        )


@router.get("/predefined/{strategy_type}", response_model=Dict[str, Any])
def get_predefined_strategy(strategy_type: str):
    """Récupérer une stratégie prédéfinie par son type"""
    try:
        strategy = PredefinedStrategies.get_strategy_by_type(strategy_type)
        
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Type de stratégie '{strategy_type}' non trouvé"
            )
        
        return {
            "success": True,
            "strategy": strategy
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération de la stratégie: {str(e)}"
        )


@router.post("/predefined/initialize", response_model=Dict[str, Any])
def initialize_predefined_strategies(db: Session = Depends(get_db)):
    """Initialiser toutes les stratégies prédéfinies"""
    try:
        strategy_service = TradingStrategyService(db)
        initializer = StrategyInitializer(strategy_service)
        
        result = initializer.initialize_all_strategies()
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'initialisation: {str(e)}"
        )


@router.post("/predefined/initialize/{strategy_type}", response_model=Dict[str, Any])
def initialize_predefined_strategy(
    strategy_type: str,
    db: Session = Depends(get_db)
):
    """Initialiser une stratégie prédéfinie spécifique"""
    try:
        strategy_service = TradingStrategyService(db)
        initializer = StrategyInitializer(strategy_service)
        
        result = initializer.initialize_strategy_by_type(strategy_type)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'initialisation: {str(e)}"
        )
