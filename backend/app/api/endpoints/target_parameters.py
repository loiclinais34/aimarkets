from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.database import TargetParameters
from app.models.schemas import (
    TargetParameter, TargetParameterCreate, TargetParameterUpdate,
    TargetPriceCalculation, MessageResponse
)
from app.services.ml_service import MLService

router = APIRouter(prefix="/target-parameters", tags=["target-parameters"])


@router.post("/", response_model=TargetParameter, status_code=status.HTTP_201_CREATED)
def create_target_parameter(
    target_param: TargetParameterCreate,
    db: Session = Depends(get_db)
):
    """Créer un nouveau paramètre de cible de rentabilité"""
    try:
        ml_service = MLService(db)
        
        # Vérifier si un paramètre avec le même nom existe déjà pour cet utilisateur
        existing = db.query(TargetParameters).filter(
            TargetParameters.user_id == target_param.user_id,
            TargetParameters.parameter_name == target_param.parameter_name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Un paramètre avec le nom '{target_param.parameter_name}' existe déjà pour cet utilisateur"
            )
        
        new_param = ml_service.create_target_parameter(
            user_id=target_param.user_id,
            parameter_name=target_param.parameter_name,
            target_return_percentage=target_param.target_return_percentage,
            time_horizon_days=target_param.time_horizon_days,
            risk_tolerance=target_param.risk_tolerance,
            min_confidence_threshold=target_param.min_confidence_threshold,
            max_drawdown_percentage=target_param.max_drawdown_percentage
        )
        
        return new_param
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du paramètre: {str(e)}"
        )


@router.get("/user/{user_id}", response_model=List[TargetParameter])
def get_user_target_parameters(
    user_id: str,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Récupérer les paramètres de cible pour un utilisateur"""
    try:
        ml_service = MLService(db)
        
        if active_only:
            params = ml_service.get_target_parameters(user_id)
        else:
            params = db.query(TargetParameters).filter(
                TargetParameters.user_id == user_id
            ).all()
        
        return params
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des paramètres: {str(e)}"
        )


@router.get("/{param_id}", response_model=TargetParameter)
def get_target_parameter(
    param_id: int,
    db: Session = Depends(get_db)
):
    """Récupérer un paramètre de cible par ID"""
    try:
        param = db.query(TargetParameters).filter(
            TargetParameters.id == param_id
        ).first()
        
        if not param:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paramètre de cible non trouvé"
            )
        
        return param
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du paramètre: {str(e)}"
        )


@router.put("/{param_id}", response_model=TargetParameter)
def update_target_parameter(
    param_id: int,
    param_update: TargetParameterUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour un paramètre de cible"""
    try:
        param = db.query(TargetParameters).filter(
            TargetParameters.id == param_id
        ).first()
        
        if not param:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paramètre de cible non trouvé"
            )
        
        # Mettre à jour les champs fournis
        update_data = param_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(param, field, value)
        
        param.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(param)
        
        return param
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour du paramètre: {str(e)}"
        )


@router.delete("/{param_id}", response_model=MessageResponse)
def delete_target_parameter(
    param_id: int,
    db: Session = Depends(get_db)
):
    """Supprimer un paramètre de cible (désactivation)"""
    try:
        param = db.query(TargetParameters).filter(
            TargetParameters.id == param_id
        ).first()
        
        if not param:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paramètre de cible non trouvé"
            )
        
        # Désactiver au lieu de supprimer
        param.is_active = False
        param.updated_at = datetime.utcnow()
        db.commit()
        
        return MessageResponse(
            message=f"Paramètre '{param.parameter_name}' désactivé avec succès"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression du paramètre: {str(e)}"
        )


@router.post("/calculate-target-price", response_model=TargetPriceCalculation)
def calculate_target_price(
    current_price: float,
    target_return_percentage: float,
    time_horizon_days: int,
    db: Session = Depends(get_db)
):
    """Calculer le prix cible basé sur le rendement attendu"""
    try:
        if current_price <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le prix actuel doit être positif"
            )
        
        if target_return_percentage < 0 or target_return_percentage > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le rendement cible doit être entre 0 et 100%"
            )
        
        if time_horizon_days < 1 or time_horizon_days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="L'horizon temporel doit être entre 1 et 365 jours"
            )
        
        ml_service = MLService(db)
        
        # Calculer le prix cible
        target_price = ml_service.calculate_target_price(
            current_price, target_return_percentage, time_horizon_days
        )
        
        # Calculer le rendement quotidien équivalent
        daily_return = (1 + target_return_percentage / 100) ** (1 / time_horizon_days) - 1
        
        # Calculer le rendement attendu
        expected_return = ((target_price - current_price) / current_price) * 100
        
        return TargetPriceCalculation(
            current_price=current_price,
            target_return_percentage=target_return_percentage,
            time_horizon_days=time_horizon_days,
            target_price=target_price,
            expected_return=expected_return,
            daily_return=daily_return * 100  # Convertir en pourcentage
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul du prix cible: {str(e)}"
        )


@router.get("/", response_model=List[TargetParameter])
def list_all_target_parameters(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Lister tous les paramètres de cible (avec pagination)"""
    try:
        query = db.query(TargetParameters)
        
        if active_only:
            query = query.filter(TargetParameters.is_active == True)
        
        params = query.offset(skip).limit(limit).all()
        
        return params
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des paramètres: {str(e)}"
        )


@router.get("/user/{user_id}/stats")
def get_user_target_parameters_stats(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Obtenir des statistiques sur les paramètres de cible d'un utilisateur"""
    try:
        # Compter les paramètres actifs et inactifs
        active_count = db.query(TargetParameters).filter(
            TargetParameters.user_id == user_id,
            TargetParameters.is_active == True
        ).count()
        
        inactive_count = db.query(TargetParameters).filter(
            TargetParameters.user_id == user_id,
            TargetParameters.is_active == False
        ).count()
        
        # Obtenir les statistiques des rendements cibles
        params = db.query(TargetParameters).filter(
            TargetParameters.user_id == user_id,
            TargetParameters.is_active == True
        ).all()
        
        if params:
            target_returns = [p.target_return_percentage for p in params]
            time_horizons = [p.time_horizon_days for p in params]
            
            stats = {
                "total_active": active_count,
                "total_inactive": inactive_count,
                "target_return_stats": {
                    "min": min(target_returns),
                    "max": max(target_returns),
                    "avg": sum(target_returns) / len(target_returns),
                    "count": len(target_returns)
                },
                "time_horizon_stats": {
                    "min": min(time_horizons),
                    "max": max(time_horizons),
                    "avg": sum(time_horizons) / len(time_horizons),
                    "count": len(time_horizons)
                }
            }
        else:
            stats = {
                "total_active": active_count,
                "total_inactive": inactive_count,
                "target_return_stats": None,
                "time_horizon_stats": None
            }
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul des statistiques: {str(e)}"
        )
