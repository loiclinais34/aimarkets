"""
Schémas pour la pipeline d'analyse avancée
"""

from pydantic import BaseModel, Field
from typing import List, Optional

class PipelineStartRequest(BaseModel):
    """Requête pour démarrer la pipeline"""
    force_update: bool = Field(default=False, description="Forcer la mise à jour")
    symbols: Optional[List[str]] = Field(default=None, description="Liste des symboles à traiter")

class IndicatorsCalculationRequest(BaseModel):
    """Requête pour le calcul des indicateurs"""
    symbols: List[str] = Field(..., description="Liste des symboles à traiter")
    force_update: bool = Field(default=False, description="Forcer le recalcul")

class OpportunitiesAnalysisRequest(BaseModel):
    """Requête pour l'analyse des opportunités"""
    symbols: List[str] = Field(..., description="Liste des symboles à analyser")

