"""
Encodeur JSON personnalisé pour gérer les types NumPy et pandas.
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, date
from decimal import Decimal
from typing import Any


class NumpyEncoder(json.JSONEncoder):
    """
    Encodeur JSON personnalisé pour gérer les types NumPy, pandas et autres types non sérialisables.
    """
    
    def default(self, obj: Any) -> Any:
        """
        Convertit les objets non sérialisables en types JSON valides.
        
        Args:
            obj: Objet à sérialiser
            
        Returns:
            Version sérialisable de l'objet
        """
        # Types NumPy
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        
        # Types pandas
        elif isinstance(obj, pd.Series):
            # Pour les séries pandas, prendre la dernière valeur ou convertir en liste
            if len(obj) > 0:
                last_val = obj.iloc[-1]
                if pd.isna(last_val):
                    return None
                return float(last_val) if isinstance(last_val, (int, float, np.number)) else str(last_val)
            return None
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        
        # Types datetime
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        
        # Types Decimal
        elif isinstance(obj, Decimal):
            return float(obj)
        
        # Types complexes
        elif isinstance(obj, complex):
            return {"real": obj.real, "imag": obj.imag}
        
        # Fallback pour les autres types
        return super().default(obj)


def safe_json_serialize(obj: Any) -> str:
    """
    Sérialise un objet en JSON de manière sécurisée.
    
    Args:
        obj: Objet à sérialiser
        
    Returns:
        Chaîne JSON
    """
    return json.dumps(obj, cls=NumpyEncoder, indent=2)


def safe_json_deserialize(json_str: str) -> Any:
    """
    Désérialise une chaîne JSON.
    
    Args:
        json_str: Chaîne JSON
        
    Returns:
        Objet Python
    """
    return json.loads(json_str)


def make_json_safe(obj: Any) -> Any:
    """
    Convertit un objet en version sérialisable JSON.
    
    Args:
        obj: Objet à convertir
        
    Returns:
        Version sérialisable de l'objet
    """
    if isinstance(obj, dict):
        return {key: make_json_safe(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, pd.Series):
        if len(obj) > 0:
            last_val = obj.iloc[-1]
            if pd.isna(last_val):
                return None
            return float(last_val) if isinstance(last_val, (int, float, np.number)) else str(last_val)
        return None
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict('records')
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, complex):
        return {"real": obj.real, "imag": obj.imag}
    else:
        return obj
