"""
Endpoints d'authentification
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.services.authentication_service import AuthenticationService
from app.services.user_service import UserService

router = APIRouter()
security = HTTPBearer()


# ==================== MODÈLES PYDANTIC ====================

class UserRegistration(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: str
    last_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_at: datetime
    user: dict


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    created_at: datetime


# ==================== DÉPENDANCES ====================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Dépendance pour récupérer l'utilisateur actuel"""
    
    auth_service = AuthenticationService(db)
    user = auth_service.validate_session(credentials.credentials)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def require_role(required_role: str):
    """Dépendance pour vérifier un rôle spécifique"""
    
    def role_checker(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
        auth_service = AuthenticationService(db)
        auth_service.require_role(current_user, required_role)
        return current_user
    
    return role_checker


# ==================== ENDPOINTS ====================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegistration,
    db: Session = Depends(get_db)
):
    """Enregistre un nouvel utilisateur"""
    
    user_service = UserService(db)
    
    # Valider le mot de passe
    password_validation = user_service.validate_password_strength(user_data.password)
    if not password_validation["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Mot de passe non conforme",
                "errors": password_validation["errors"]
            }
        )
    
    try:
        user = user_service.create_user(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name
        )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de l'utilisateur: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Authentifie un utilisateur et retourne un token de session"""
    
    auth_service = AuthenticationService(db)
    
    user = auth_service.authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Créer une nouvelle session
    session_token = auth_service.create_session(user.id)
    
    # Calculer la date d'expiration
    expires_at = datetime.utcnow() + auth_service.SESSION_LIFETIME
    
    return TokenResponse(
        access_token=session_token,
        token_type="bearer",
        expires_at=expires_at,
        user={
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role
        }
    )


@router.post("/logout")
async def logout_user(
    current_user = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Déconnecte l'utilisateur actuel"""
    
    auth_service = AuthenticationService(db)
    auth_service.revoke_session(credentials.credentials)
    
    return {"message": "Déconnexion réussie"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """Retourne les informations de l'utilisateur actuel"""
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.post("/password-reset-request")
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Demande une réinitialisation de mot de passe"""
    
    auth_service = AuthenticationService(db)
    token = auth_service.create_password_reset_token(reset_request.email)
    
    # Dans un vrai système, on enverrait l'email avec le token
    # Ici, on retourne juste le token pour les tests
    return {
        "message": "Si l'email existe, un lien de réinitialisation a été envoyé",
        "token": token  # À supprimer en production
    }


@router.post("/password-reset")
async def reset_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """Réinitialise le mot de passe avec un token"""
    
    user_service = UserService(db)
    
    # Valider le nouveau mot de passe
    password_validation = user_service.validate_password_strength(reset_data.new_password)
    if not password_validation["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Mot de passe non conforme",
                "errors": password_validation["errors"]
            }
        )
    
    success = user_service.reset_password(reset_data.token, reset_data.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalide ou expiré"
        )
    
    return {"message": "Mot de passe réinitialisé avec succès"}


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change le mot de passe de l'utilisateur actuel"""
    
    user_service = UserService(db)
    
    # Valider le nouveau mot de passe
    password_validation = user_service.validate_password_strength(password_data.new_password)
    if not password_validation["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Mot de passe non conforme",
                "errors": password_validation["errors"]
            }
        )
    
    success = user_service.change_password(
        current_user.id,
        password_data.current_password,
        password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe actuel incorrect"
        )
    
    return {"message": "Mot de passe modifié avec succès"}


@router.post("/logout-all")
async def logout_all_sessions(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Déconnecte l'utilisateur de toutes ses sessions"""
    
    auth_service = AuthenticationService(db)
    revoked_count = auth_service.revoke_all_user_sessions(current_user.id)
    
    return {
        "message": f"Toutes les sessions ont été révoquées",
        "revoked_sessions": revoked_count
    }


@router.get("/stats")
async def get_user_stats(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retourne les statistiques de l'utilisateur actuel"""
    
    auth_service = AuthenticationService(db)
    stats = auth_service.get_user_stats(current_user.id)
    
    return stats
