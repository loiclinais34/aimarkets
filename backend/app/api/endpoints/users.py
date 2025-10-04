"""
Endpoints de gestion des utilisateurs (admin)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.services.user_service import UserService
from app.services.authentication_service import AuthenticationService
from app.api.endpoints.auth import get_current_user, require_role

router = APIRouter()


# ==================== MODÈLES PYDANTIC ====================

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    created_at: str
    updated_at: str


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    skip: int
    limit: int


class UserStatsResponse(BaseModel):
    total_users: int
    active_users: int
    users_by_role: dict


# ==================== ENDPOINTS ====================

@router.get("/", response_model=UserListResponse)
async def get_users(
    skip: int = Query(0, ge=0, description="Nombre d'utilisateurs à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'utilisateurs à retourner"),
    search: Optional[str] = Query(None, description="Recherche dans nom, email, prénom, nom de famille"),
    role: Optional[str] = Query(None, description="Filtrer par rôle"),
    is_active: Optional[bool] = Query(None, description="Filtrer par statut actif"),
    current_user = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db)
):
    """Récupère la liste des utilisateurs (admin uniquement)"""
    
    user_service = UserService(db)
    
    # Récupérer les utilisateurs
    users = user_service.get_all_users(
        skip=skip,
        limit=limit,
        search=search,
        role=role,
        is_active=is_active
    )
    
    # Compter le total (pour la pagination)
    total = user_service.get_user_count()
    
    return UserListResponse(
        users=[
            UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at.isoformat(),
                updated_at=user.updated_at.isoformat()
            )
            for user in users
        ],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db)
):
    """Récupère un utilisateur par son ID (admin uniquement)"""
    
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat()
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db)
):
    """Met à jour un utilisateur (admin uniquement)"""
    
    user_service = UserService(db)
    
    try:
        updated_user = user_service.update_user(
            user_id=user_id,
            email=user_update.email,
            username=user_update.username,
            first_name=user_update.first_name,
            last_name=user_update.last_name,
            role=user_update.role,
            is_active=user_update.is_active
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur non trouvé"
            )
        
        return UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            username=updated_user.username,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            role=updated_user.role,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at.isoformat(),
            updated_at=updated_user.updated_at.isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    current_user = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db)
):
    """Active un utilisateur (admin uniquement)"""
    
    user_service = UserService(db)
    success = user_service.activate_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    return {"message": "Utilisateur activé avec succès"}


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    current_user = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db)
):
    """Désactive un utilisateur (admin uniquement)"""
    
    user_service = UserService(db)
    success = user_service.deactivate_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    return {"message": "Utilisateur désactivé avec succès"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db)
):
    """Supprime un utilisateur (admin uniquement)"""
    
    user_service = UserService(db)
    success = user_service.delete_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    return {"message": "Utilisateur supprimé avec succès"}


@router.get("/stats/overview", response_model=UserStatsResponse)
async def get_user_stats(
    current_user = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db)
):
    """Retourne les statistiques des utilisateurs (admin uniquement)"""
    
    user_service = UserService(db)
    
    total_users = user_service.get_user_count()
    active_users = user_service.get_active_user_count()
    users_by_role = user_service.get_users_by_role()
    
    return UserStatsResponse(
        total_users=total_users,
        active_users=active_users,
        users_by_role=users_by_role
    )


@router.get("/recent/new")
async def get_recent_users(
    days: int = Query(30, ge=1, le=365, description="Nombre de jours à considérer"),
    current_user = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db)
):
    """Retourne les utilisateurs créés récemment (admin uniquement)"""
    
    user_service = UserService(db)
    recent_users = user_service.get_recent_users(days)
    
    return {
        "users": [
            UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at.isoformat(),
                updated_at=user.updated_at.isoformat()
            )
            for user in recent_users
        ],
        "period_days": days,
        "count": len(recent_users)
    }


@router.get("/{user_id}/activity")
async def get_user_activity(
    user_id: int,
    current_user = Depends(require_role("ADMIN")),
    db: Session = Depends(get_db)
):
    """Retourne les statistiques d'activité d'un utilisateur (admin uniquement)"""
    
    user_service = UserService(db)
    
    # Vérifier que l'utilisateur existe
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    activity_stats = user_service.get_user_activity_stats(user_id)
    
    return activity_stats
