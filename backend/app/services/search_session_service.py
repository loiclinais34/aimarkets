"""
Service pour gérer les sessions de recherche d'opportunités
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.database import SearchSession, ScreenerResult, MLModels
from ..models.schemas import SearchSessionCreate, SearchSessionUpdate


class SearchSessionService:
    def __init__(self, db: Session):
        self.db = db

    def create_search_session(
        self,
        target_return_percentage: float,
        time_horizon_days: int,
        risk_tolerance: float,
        confidence_threshold: float
    ) -> SearchSession:
        """Créer une nouvelle session de recherche"""
        search_id = str(uuid.uuid4())
        
        search_session = SearchSession(
            search_id=search_id,
            target_return_percentage=target_return_percentage,
            time_horizon_days=time_horizon_days,
            risk_tolerance=risk_tolerance,
            confidence_threshold=confidence_threshold,
            status='pending'
        )
        
        self.db.add(search_session)
        self.db.commit()
        self.db.refresh(search_session)
        
        return search_session

    def get_search_session(self, search_id: str) -> Optional[SearchSession]:
        """Récupérer une session de recherche par son ID"""
        return self.db.query(SearchSession).filter(
            SearchSession.search_id == search_id
        ).first()

    def update_search_session_status(
        self,
        search_id: str,
        status: str,
        total_opportunities: Optional[int] = None
    ) -> Optional[SearchSession]:
        """Mettre à jour le statut d'une session de recherche"""
        search_session = self.get_search_session(search_id)
        if not search_session:
            return None
        
        search_session.status = status
        if total_opportunities is not None:
            search_session.total_opportunities = total_opportunities
        
        if status == 'completed':
            search_session.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(search_session)
        
        return search_session

    def get_search_opportunities(self, search_id: str) -> list:
        """Récupérer toutes les opportunités d'une session de recherche"""
        opportunities = self.db.query(ScreenerResult).filter(
            ScreenerResult.search_id == search_id
        ).order_by(ScreenerResult.rank.asc()).all()
        
        return opportunities

    def get_search_models(self, search_id: str) -> list:
        """Récupérer tous les modèles d'une session de recherche"""
        models = self.db.query(MLModels).filter(
            MLModels.search_id == search_id
        ).all()
        
        return models

    def get_latest_search_sessions(self, limit: int = 10) -> list:
        """Récupérer les dernières sessions de recherche"""
        return self.db.query(SearchSession).order_by(
            SearchSession.created_at.desc()
        ).limit(limit).all()

    def get_search_session_stats(self, search_id: str) -> Dict[str, Any]:
        """Récupérer les statistiques d'une session de recherche"""
        search_session = self.get_search_session(search_id)
        if not search_session:
            return {}
        
        opportunities = self.get_search_opportunities(search_id)
        models = self.get_search_models(search_id)
        
        # Compter les opportunités par symbole
        symbols_count = {}
        for opp in opportunities:
            if opp.symbol not in symbols_count:
                symbols_count[opp.symbol] = 0
            symbols_count[opp.symbol] += 1
        
        # Compter les modèles par type
        model_types_count = {}
        for model in models:
            if model.model_type not in model_types_count:
                model_types_count[model.model_type] = 0
            model_types_count[model.model_type] += 1
        
        return {
            'search_session': search_session,
            'total_opportunities': len(opportunities),
            'total_models': len(models),
            'unique_symbols': len(symbols_count),
            'symbols_count': symbols_count,
            'model_types_count': model_types_count,
            'avg_confidence': sum(opp.confidence for opp in opportunities) / len(opportunities) if opportunities else 0
        }

    def delete_search_session(self, search_id: str) -> bool:
        """Supprimer une session de recherche et ses données associées"""
        search_session = self.get_search_session(search_id)
        if not search_session:
            return False
        
        # Supprimer les opportunités associées
        self.db.query(ScreenerResult).filter(
            ScreenerResult.search_id == search_id
        ).delete()
        
        # Supprimer les modèles associés
        self.db.query(MLModels).filter(
            MLModels.search_id == search_id
        ).delete()
        
        # Supprimer la session
        self.db.delete(search_session)
        self.db.commit()
        
        return True

    def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """Nettoyer les anciennes sessions de recherche"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        old_sessions = self.db.query(SearchSession).filter(
            and_(
                SearchSession.created_at < cutoff_date,
                SearchSession.status.in_(['completed', 'failed'])
            )
        ).all()
        
        deleted_count = 0
        for session in old_sessions:
            if self.delete_search_session(session.search_id):
                deleted_count += 1
        
        return deleted_count
