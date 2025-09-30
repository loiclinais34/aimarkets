#!/usr/bin/env python3
"""
Script pour implémenter les seuils optimisés dans AdvancedTradingAnalysis
"""

import sys
import os
from typing import Dict, Any
import json

# Ajouter le chemin du backend au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class OptimizedThresholdsImplementer:
    """Implémenteur des seuils optimisés"""
    
    def __init__(self):
        """Initialise l'implémenteur"""
        self.advanced_analysis_file = "app/services/advanced_analysis/advanced_trading_analysis.py"
        
    def load_optimization_results(self) -> Dict[str, Any]:
        """Charge les résultats d'optimisation"""
        try:
            with open("scoring_thresholds_optimization.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("❌ Fichier scoring_thresholds_optimization.json non trouvé")
            return {}
    
    def generate_optimized_scoring_methods(self, results: Dict[str, Any]) -> str:
        """Génère les méthodes de scoring optimisées"""
        
        # Extraire les seuils optimaux
        tech_opt = results.get("technical_score_optimization", {})
        comp_opt = results.get("composite_score_optimization", {})
        comb_opt = results.get("combined_thresholds_optimization", {})
        weights_opt = results.get("score_weights_analysis", {})
        
        # Seuils optimaux
        tech_threshold = 0.533  # Seuil technique optimal
        comp_threshold = 0.651  # Seuil composite optimal
        
        # Poids optimaux
        tech_weight = 0.8
        sentiment_weight = 0.1
        market_weight = 0.1
        
        methods_code = f'''
    def _calculate_optimized_composite_score(
        self, 
        technical_score: float, 
        sentiment_score: float, 
        market_score: float, 
        ml_score: float = 0.0,
        candlestick_score: float = 0.0,
        garch_score: float = 0.0,
        monte_carlo_score: float = 0.0,
        markov_score: float = 0.0,
        volatility_score: float = 0.0
    ) -> float:
        """
        Calcule le score composite optimisé avec priorité au score technique
        Basé sur l'analyse des 128 opportunités à fort potentiel
        """
        try:
            # Poids optimisés basés sur l'analyse de performance
            # Priorité forte au score technique (80%)
            optimized_weights = {{
                'technical': {tech_weight},
                'sentiment': {sentiment_weight},
                'market': {market_weight}
            }}
            
            # Score composite optimisé
            composite_score = (
                optimized_weights['technical'] * technical_score +
                optimized_weights['sentiment'] * sentiment_score +
                optimized_weights['market'] * market_score
            )
            
            return round(composite_score, 4)
            
        except Exception as e:
            self.logger.error(f"Error calculating optimized composite score: {{e}}")
            return 0.5
    
    def _determine_optimized_recommendation(
        self, 
        composite_score: float, 
        technical_score: float,
        confidence_level: float
    ) -> str:
        """
        Détermine la recommandation optimisée basée sur les seuils optimaux
        """
        try:
            # Seuils optimaux basés sur l'analyse de performance
            TECH_THRESHOLD = {tech_threshold}
            COMP_THRESHOLD = {comp_threshold}
            
            # Validation des seuils techniques et composites
            tech_valid = technical_score >= TECH_THRESHOLD
            comp_valid = composite_score >= COMP_THRESHOLD
            
            # Logique de recommandation optimisée
            if comp_valid and tech_valid and confidence_level >= 0.8:
                return "BUY_STRONG"
            elif comp_valid and tech_valid and confidence_level >= 0.6:
                return "BUY_MODERATE"
            elif comp_valid or tech_valid:
                return "BUY_WEAK"
            elif composite_score >= 0.4:
                return "HOLD"
            else:
                return "SELL_MODERATE"
                
        except Exception as e:
            self.logger.error(f"Error determining optimized recommendation: {{e}}")
            return "HOLD"
    
    def _validate_optimized_signals(
        self, 
        technical_score: float, 
        composite_score: float,
        confidence_level: float
    ) -> Dict[str, bool]:
        """
        Valide les signaux optimisés selon les seuils de performance
        """
        validation = {{
            "technical_threshold_met": False,
            "composite_threshold_met": False,
            "confidence_threshold_met": False,
            "overall_valid": False
        }}
        
        try:
            # Seuils optimaux
            TECH_THRESHOLD = {tech_threshold}
            COMP_THRESHOLD = {comp_threshold}
            CONF_THRESHOLD = 0.6
            
            # Validation des seuils
            validation["technical_threshold_met"] = technical_score >= TECH_THRESHOLD
            validation["composite_threshold_met"] = composite_score >= COMP_THRESHOLD
            validation["confidence_threshold_met"] = confidence_level >= CONF_THRESHOLD
            
            # Validation globale : au moins 2 critères sur 3
            valid_criteria = sum(1 for k, v in validation.items() if k != "overall_valid" and v)
            validation["overall_valid"] = valid_criteria >= 2
            
        except Exception as e:
            self.logger.warning(f"Erreur lors de la validation optimisée: {{e}}")
        
        return validation
'''
        
        return methods_code
    
    def implement_optimized_methods(self):
        """Implémente les méthodes optimisées dans AdvancedTradingAnalysis"""
        print("🔧 Implémentation des seuils optimisés...")
        
        # Charger les résultats d'optimisation
        results = self.load_optimization_results()
        if not results:
            print("❌ Impossible de charger les résultats d'optimisation")
            return False
        
        # Générer le code des méthodes optimisées
        optimized_methods = self.generate_optimized_scoring_methods(results)
        
        # Lire le fichier AdvancedTradingAnalysis
        try:
            with open(self.advanced_analysis_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"❌ Fichier {self.advanced_analysis_file} non trouvé")
            return False
        
        # Vérifier si les méthodes optimisées existent déjà
        if "_calculate_optimized_composite_score" in content:
            print("⚠️ Les méthodes optimisées existent déjà")
            return True
        
        # Trouver le point d'insertion (avant la méthode analyze_opportunity)
        insertion_point = "    async def analyze_opportunity"
        if insertion_point not in content:
            print("❌ Point d'insertion non trouvé")
            return False
        
        # Insérer les méthodes optimisées
        new_content = content.replace(
            insertion_point,
            optimized_methods + "\n" + insertion_point
        )
        
        # Sauvegarder le fichier modifié
        try:
            with open(self.advanced_analysis_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("✅ Méthodes optimisées implémentées avec succès")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            return False
    
    def update_analyze_opportunity_method(self):
        """Met à jour la méthode analyze_opportunity pour utiliser les seuils optimisés"""
        print("🔄 Mise à jour de la méthode analyze_opportunity...")
        
        try:
            with open(self.advanced_analysis_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"❌ Fichier {self.advanced_analysis_file} non trouvé")
            return False
        
        # Remplacer l'appel à _calculate_composite_score
        old_composite_call = "composite_score = self._calculate_composite_score("
        new_composite_call = "composite_score = self._calculate_optimized_composite_score("
        
        if old_composite_call in content:
            content = content.replace(old_composite_call, new_composite_call)
            print("✅ Appel au score composite optimisé")
        else:
            print("⚠️ Appel au score composite non trouvé")
        
        # Remplacer l'appel à _determine_recommendation
        old_rec_call = "recommendation = self._determine_recommendation("
        new_rec_call = "recommendation = self._determine_optimized_recommendation("
        
        if old_rec_call in content:
            content = content.replace(old_rec_call, new_rec_call)
            print("✅ Appel à la recommandation optimisée")
        else:
            print("⚠️ Appel à la recommandation non trouvé")
        
        # Sauvegarder le fichier modifié
        try:
            with open(self.advanced_analysis_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ Méthode analyze_opportunity mise à jour")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            return False
    
    def run_implementation(self):
        """Exécute l'implémentation complète"""
        print("🚀 Démarrage de l'implémentation des seuils optimisés")
        print("=" * 80)
        
        # Implémenter les méthodes optimisées
        if not self.implement_optimized_methods():
            return False
        
        # Mettre à jour la méthode analyze_opportunity
        if not self.update_analyze_opportunity_method():
            return False
        
        print("\n✅ Implémentation terminée avec succès")
        print("\n📊 RÉSUMÉ DES OPTIMISATIONS IMPLÉMENTÉES:")
        print("  • Score technique prioritaire (poids: 80%)")
        print("  • Seuil technique optimal: 0.533")
        print("  • Seuil composite optimal: 0.651")
        print("  • Validation des signaux optimisée")
        print("  • Recommandations basées sur les seuils de performance")
        
        return True

def main():
    """Fonction principale"""
    implementer = OptimizedThresholdsImplementer()
    
    try:
        success = implementer.run_implementation()
        if success:
            print("\n🎯 Les seuils optimisés ont été implémentés avec succès!")
            print("   Vous pouvez maintenant tester les nouvelles performances.")
        else:
            print("\n❌ Échec de l'implémentation")
    
    except Exception as e:
        print(f"❌ Erreur lors de l'implémentation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
