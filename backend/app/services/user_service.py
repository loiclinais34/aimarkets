"""
Service de gestion des utilisateurs
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status

from app.models.users import User
from app.services.authentication_service import AuthenticationService


class UserService:
    """Service de gestion des utilisateurs"""
    
    def __init__(self, db: Session):
        self.db = db
        self.auth_service = AuthenticationService(db)
    
    # ==================== CRUD UTILISATEURS ====================
    
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
        return self.auth_service.create_user(
            email=email,
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role
        )
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Récupère un utilisateur par son ID"""
        return self.auth_service.get_user_by_id(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Récupère un utilisateur par son email"""
        return self.auth_service.get_user_by_email(email)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Récupère un utilisateur par son nom d'utilisateur"""
        return self.auth_service.get_user_by_username(username)
    
    def get_all_users(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """Récupère tous les utilisateurs avec filtres"""
        
        query = self.db.query(User)
        
        # Filtre de recherche
        if search:
            search_filter = or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Filtre par rôle
        if role:
            query = query.filter(User.role == role)
        
        # Filtre par statut actif
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def update_user(
        self,
        user_id: int,
        email: Optional[str] = None,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[User]:
        """Met à jour les informations d'un utilisateur"""
        
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Vérifier l'unicité de l'email si modifié
        if email and email != user.email:
            existing_user = self.get_user_by_email(email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Un utilisateur avec cet email existe déjà"
                )
            user.email = email
        
        # Vérifier l'unicité du nom d'utilisateur si modifié
        if username and username != user.username:
            existing_user = self.get_user_by_username(username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ce nom d'utilisateur est déjà utilisé"
                )
            user.username = username
        
        # Mettre à jour les autres champs
        if first_name is not None:
            user.first_name = first_name
        
        if last_name is not None:
            user.last_name = last_name
        
        if role is not None:
            user.role = role
        
        if is_active is not None:
            user.is_active = is_active
        
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def deactivate_user(self, user_id: int) -> bool:
        """Désactive un utilisateur"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        # Révoquer toutes les sessions
        self.auth_service.revoke_all_user_sessions(user_id)
        
        self.db.commit()
        return True
    
    def activate_user(self, user_id: int) -> bool:
        """Active un utilisateur"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_active = True
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def delete_user(self, user_id: int) -> bool:
        """Supprime un utilisateur (soft delete)"""
        return self.deactivate_user(user_id)
    
    # ==================== GESTION DES MOTS DE PASSE ====================
    
    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> bool:
        """Change le mot de passe d'un utilisateur"""
        
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Vérifier le mot de passe actuel
        if not self.auth_service.verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mot de passe actuel incorrect"
            )
        
        # Mettre à jour le mot de passe
        return self.auth_service.update_user_password(user_id, new_password)
    
    def reset_password(self, token: str, new_password: str) -> bool:
        """Réinitialise le mot de passe avec un token"""
        return self.auth_service.reset_password_with_token(token, new_password)
    
    # ==================== STATISTIQUES ET RAPPORTS ====================
    
    def get_user_count(self) -> int:
        """Retourne le nombre total d'utilisateurs"""
        return self.db.query(User).count()
    
    def get_active_user_count(self) -> int:
        """Retourne le nombre d'utilisateurs actifs"""
        return self.db.query(User).filter(User.is_active == True).count()
    
    def get_users_by_role(self) -> Dict[str, int]:
        """Retourne la répartition des utilisateurs par rôle"""
        
        from sqlalchemy import func
        
        results = self.db.query(
            User.role,
            func.count(User.id).label('count')
        ).group_by(User.role).all()
        
        return {role: count for role, count in results}
    
    def get_recent_users(self, days: int = 30) -> List[User]:
        """Retourne les utilisateurs créés récemment"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return self.db.query(User).filter(
            User.created_at >= cutoff_date
        ).order_by(User.created_at.desc()).all()
    
    def get_user_activity_stats(self, user_id: int) -> Dict[str, Any]:
        """Retourne les statistiques d'activité d'un utilisateur"""
        
        user = self.get_user_by_id(user_id)
        if not user:
            return {}
        
        # Statistiques de base
        stats = self.auth_service.get_user_stats(user_id)
        
        # Ajouter des statistiques spécifiques au service utilisateur
        # (à compléter selon les besoins)
        
        return stats
    
    # ==================== VALIDATION ====================
    
    def validate_email(self, email: str) -> bool:
        """Valide le format d'un email"""
        import re
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Valide la force d'un mot de passe"""
        
        result = {
            "is_valid": True,
            "errors": [],
            "strength": "weak"
        }
        
        # Longueur minimale
        if len(password) < 8:
            result["is_valid"] = False
            result["errors"].append("Le mot de passe doit contenir au moins 8 caractères")
        
        # Vérifications de complexité
        has_uppercase = any(c.isupper() for c in password)
        has_lowercase = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        complexity_score = sum([has_uppercase, has_lowercase, has_digit, has_special])
        
        if complexity_score >= 3:
            result["strength"] = "strong"
        elif complexity_score >= 2:
            result["strength"] = "medium"
        
        if not has_uppercase:
            result["errors"].append("Le mot de passe doit contenir au moins une majuscule")
        
        if not has_lowercase:
            result["errors"].append("Le mot de passe doit contenir au moins une minuscule")
        
        if not has_digit:
            result["errors"].append("Le mot de passe doit contenir au moins un chiffre")
        
        if not has_special:
            result["errors"].append("Le mot de passe doit contenir au moins un caractère spécial")
        
        if result["errors"]:
            result["is_valid"] = False
        
        return result


# Import nécessaire pour timedelta
from datetime import timedelta
