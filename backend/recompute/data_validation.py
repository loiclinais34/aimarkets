"""
Module de validation des données pour le recompute
"""
from typing import List
from sqlalchemy.orm import Session
from app.models.database import HistoricalData

def validate_input_data(symbols: List[str], db: Session) -> dict:
    """
    Valide la présence et qualité des données requises
    """
    validation_results = {
        "valid": True,
        "errors": []
    }
    
    # Vérifier données historiques
    for symbol in symbols:
        data_count = db.query(HistoricalData).filter(
            HistoricalData.symbol == symbol
        ).count()
        
        if data_count < 30:  # Minimum requis pour calculs
            validation_results["valid"] = False
            validation_results["errors"].append(
                f"Insufficient data for {symbol}: {data_count} records"
            )
    
    return validation_results