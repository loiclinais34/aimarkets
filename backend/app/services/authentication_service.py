"""
Service d'authentification pour la gestion des utilisateurs et sessions
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.users import User, UserSession, PasswordReset
from app.core.config import get_settings

settings = get_settings()

# Configuration du hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Durée de vie des sessions (7 jours par défaut)
SESSION_LIFETIME = timedelta(days=7)

# Durée de vie des tokens de réinitialisation (1 heure)
PASSWORD_RESET_LIFETIME = timedelta(hours=1)


class AuthenticationService:
    """Service de gestion de l'authentification"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== GESTION DES MOTS DE PASSE ====================
    
    def hash_password(self, password: str) -> str:
        """Hache un mot de passe"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Vérifie un mot de passe contre son hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    # ==================== GESTION DES UTILISATEURS ====================
    
    def create_user(
        self,
        email: str,
        username: str,
        password: str,
        first_name: str,
        last_name: str,
        role: str = "MEMBER"
    ) -> User:
        """Crée un nouvel utilisateur"""
        
        # Vérifier si l'email existe déjà
        if self.get_user_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un utilisateur avec cet email existe déjà"
            )
        
        # Vérifier si le nom d'utilisateur existe déjà
        if self.get_user_by_username(username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ce nom d'utilisateur est déjà utilisé"
            )
        
        # Créer l'utilisateur
        hashed_password = self.hash_password(password)
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=True
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Récupère un utilisateur par son ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Récupère un utilisateur par son email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Récupère un utilisateur par son nom d'utilisateur"""
        return self.db.query(User).filter(User.username == username).first()
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authentifie un utilisateur avec email et mot de passe"""
        user = self.get_user_by_email(email)
        if not user:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        return user
    
    def update_user_password(self, user_id: int, new_password: str) -> bool:
        """Met à jour le mot de passe d'un utilisateur"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.hashed_password = self.hash_password(new_password)
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    # ==================== GESTION DES SESSIONS ====================
    
    def create_session(self, user_id: int) -> str:
        """Crée une nouvelle session pour un utilisateur"""
        
        # Générer un token de session sécurisé
        session_token = secrets.token_urlsafe(32)
        
        # Calculer la date d'expiration
        expires_at = datetime.utcnow() + SESSION_LIFETIME
        
        # Créer la session
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            expires_at=expires_at
        )
        
        self.db.add(session)
        self.db.commit()
        
        return session_token
    
    def validate_session(self, session_token: str) -> Optional[User]:
        """Valide un token de session et retourne l'utilisateur"""
        
        session = self.db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.expires_at > datetime.utcnow()
        ).first()
        
        if not session:
            return None
        
        # Récupérer l'utilisateur
        user = self.get_user_by_id(session.user_id)
        if not user or not user.is_active:
            return None
        
        return user
    
    def revoke_session(self, session_token: str) -> bool:
        """Révoque une session"""
        session = self.db.query(UserSession).filter(
            UserSession.session_token == session_token
        ).first()
        
        if session:
            self.db.delete(session)
            self.db.commit()
            return True
        
        return False
    
    def revoke_all_user_sessions(self, user_id: int) -> int:
        """Révoque toutes les sessions d'un utilisateur"""
        deleted_count = self.db.query(UserSession).filter(
            UserSession.user_id == user_id
        ).delete()
        
        self.db.commit()
        return deleted_count
    
    def cleanup_expired_sessions(self) -> int:
        """Nettoie les sessions expirées"""
        deleted_count = self.db.query(UserSession).filter(
            UserSession.expires_at <= datetime.utcnow()
        ).delete()
        
        self.db.commit()
        return deleted_count
    
    # ==================== RÉINITIALISATION DE MOT DE PASSE ====================
    
    def create_password_reset_token(self, email: str) -> Optional[str]:
        """Crée un token de réinitialisation de mot de passe"""
        
        user = self.get_user_by_email(email)
        if not user:
            # Ne pas révéler si l'email existe ou non
            return None
        
        # Générer un token sécurisé
        reset_token = secrets.token_urlsafe(32)
        
        # Calculer la date d'expiration
        expires_at = datetime.utcnow() + PASSWORD_RESET_LIFETIME
        
        # Créer l'enregistrement de réinitialisation
        password_reset = PasswordReset(
            user_id=user.id,
            token=reset_token,
            expires_at=expires_at
        )
        
        self.db.add(password_reset)
        self.db.commit()
        
        return reset_token
    
    def validate_password_reset_token(self, token: str) -> Optional[User]:
        """Valide un token de réinitialisation de mot de passe"""
        
        reset_record = self.db.query(PasswordReset).filter(
            PasswordReset.token == token,
            PasswordReset.expires_at > datetime.utcnow()
        ).first()
        
        if not reset_record:
            return None
        
        # Récupérer l'utilisateur
        user = self.get_user_by_id(reset_record.user_id)
        if not user or not user.is_active:
            return None
        
        return user
    
    def reset_password_with_token(self, token: str, new_password: str) -> bool:
        """Réinitialise le mot de passe avec un token"""
        
        user = self.validate_password_reset_token(token)
        if not user:
            return False
        
        # Mettre à jour le mot de passe
        user.hashed_password = self.hash_password(new_password)
        user.updated_at = datetime.utcnow()
        
        # Supprimer le token de réinitialisation
        self.db.query(PasswordReset).filter(
            PasswordReset.token == token
        ).delete()
        
        # Révoquer toutes les sessions existantes
        self.revoke_all_user_sessions(user.id)
        
        self.db.commit()
        return True
    
    def cleanup_expired_password_resets(self) -> int:
        """Nettoie les tokens de réinitialisation expirés"""
        deleted_count = self.db.query(PasswordReset).filter(
            PasswordReset.expires_at <= datetime.utcnow()
        ).delete()
        
        self.db.commit()
        return deleted_count
    
    # ==================== GESTION DES RÔLES ====================
    
    def has_role(self, user: User, required_role: str) -> bool:
        """Vérifie si un utilisateur a un rôle spécifique"""
        
        role_hierarchy = {
            "ADMIN": 3,
            "PREMIUM": 2,
            "MEMBER": 1
        }
        
        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    def require_role(self, user: User, required_role: str) -> None:
        """Lève une exception si l'utilisateur n'a pas le rôle requis"""
        if not self.has_role(user, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rôle {required_role} requis"
            )
    
    # ==================== UTILITAIRES ====================
    
    def get_user_stats(self, user_id: int) -> dict:
        """Retourne les statistiques d'un utilisateur"""
        
        user = self.get_user_by_id(user_id)
        if not user:
            return {}
        
        # Compter les sessions actives
        active_sessions = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.expires_at > datetime.utcnow()
        ).count()
        
        return {
            "user_id": user_id,
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "is_active": user.is_active,
            "active_sessions": active_sessions,
            "created_at": user.created_at,
            "last_login": user.updated_at
        }
