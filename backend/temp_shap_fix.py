    def calculate_shap_explanations(self, model_id: int, symbol: str, prediction_date: date, db: Session = None) -> Dict:
        """Calculer les explications SHAP pour une prédiction - DÉSACTIVÉ"""
        return {
            "error": "SHAP désactivé temporairement pour éviter les conflits NumPy",
            "shap_explanations": [],
            "feature_importance": []
        }
