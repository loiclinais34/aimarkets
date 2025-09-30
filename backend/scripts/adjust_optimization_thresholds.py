#!/usr/bin/env python3
"""
Script pour ajuster les seuils d'optimisation pour qu'ils soient plus réalistes
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any
import json

# Ajouter le chemin du backend au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class OptimizationThresholdsAdjuster:
    """Ajusteur des seuils d'optimisation"""
    
    def __init__(self):
        """Initialise l'ajusteur"""
        self.advanced_analysis_file = "app/services/advanced_analysis/advanced_trading_analysis.py"
        
    def generate_adjusted_thresholds(self) -> str:
        """Génère les seuils ajustés plus réalistes"""
        
        # Seuils ajustés basés sur l'analyse des données réelles
        # Les seuils précédents étaient trop stricts (0.533, 0.651, 0.6)
        # Ajustons-les pour être plus réalistes tout en gardant la qualité
        
        TECH_THRESHOLD = 0.45  # Réduit de 0.533 à 0.45
        COMP_THRESHOLD = 0.50  # Réduit de 0.651 à 0.50
        CONF_THRESHOLD = 0.6   # Maintenu à 0.6
        
        methods_code = f'''
    def _calculate_adjusted_optimized_composite_score(
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
        Calcule le score composite avec priorité au score technique (80%)
        Seuils ajustés pour être plus réalistes
        """
        try:
            # Poids optimisés - priorité forte au score technique
            priority_weights = {{
                'technical': 0.8,      # 80% - priorité maximale
                'sentiment': 0.1,      # 10%
                'market': 0.1          # 10%
            }}
            
            # Score composite avec priorité technique
            composite_score = (
                priority_weights['technical'] * technical_score +
                priority_weights['sentiment'] * sentiment_score +
                priority_weights['market'] * market_score
            )
            
            return round(composite_score, 4)
            
        except Exception as e:
            self.logger.error(f"Error calculating adjusted optimized composite score: {{e}}")
            return 0.5
    
    def _determine_adjusted_optimized_recommendation(
        self, 
        composite_score: float, 
        technical_score: float,
        confidence_level: float
    ) -> str:
        """
        Détermine la recommandation avec les seuils ajustés
        Seuils plus réalistes basés sur l'analyse des données
        """
        try:
            # Seuils ajustés plus réalistes
            TECH_THRESHOLD = {TECH_THRESHOLD}
            COMP_THRESHOLD = {COMP_THRESHOLD}
            CONF_THRESHOLD = {CONF_THRESHOLD}
            
            # Validation des seuils ajustés
            tech_valid = technical_score >= TECH_THRESHOLD
            comp_valid = composite_score >= COMP_THRESHOLD
            conf_valid = confidence_level >= CONF_THRESHOLD
            
            # Logique de recommandation avec seuils ajustés
            if comp_valid and tech_valid and conf_valid:
                return "BUY_STRONG"
            elif comp_valid and tech_valid:
                return "BUY_MODERATE"
            elif comp_valid or tech_valid:
                return "BUY_WEAK"
            elif composite_score >= 0.4:
                return "HOLD"
            else:
                return "SELL_MODERATE"
                
        except Exception as e:
            self.logger.error(f"Error determining adjusted optimized recommendation: {{e}}")
            return "HOLD"
    
    def _validate_adjusted_optimized_signals(
        self, 
        technical_score: float, 
        composite_score: float,
        confidence_level: float
    ) -> Dict[str, bool]:
        """
        Valide les signaux avec les seuils ajustés
        Seuils plus réalistes pour une meilleure sélection
        """
        validation = {{
            "technical_threshold_met": False,
            "composite_threshold_met": False,
            "confidence_threshold_met": False,
            "overall_valid": False
        }}
        
        try:
            # Seuils ajustés
            TECH_THRESHOLD = {TECH_THRESHOLD}
            COMP_THRESHOLD = {COMP_THRESHOLD}
            CONF_THRESHOLD = {CONF_THRESHOLD}
            
            # Validation des seuils
            validation["technical_threshold_met"] = technical_score >= TECH_THRESHOLD
            validation["composite_threshold_met"] = composite_score >= COMP_THRESHOLD
            validation["confidence_threshold_met"] = confidence_level >= CONF_THRESHOLD
            
            # Validation globale : au moins 2 critères sur 3
            valid_criteria = sum(1 for k, v in validation.items() if k != "overall_valid" and v)
            validation["overall_valid"] = valid_criteria >= 2
            
        except Exception as e:
            self.logger.warning(f"Erreur lors de la validation ajustée: {{e}}")
        
        return validation
    
    def _apply_adjusted_optimized_filtering(
        self, 
        technical_score: float, 
        composite_score: float,
        confidence_level: float
    ) -> bool:
        """
        Applique le filtrage ajusté pour ne garder que les opportunités de qualité
        Seuils plus réalistes pour une meilleure sélection
        """
        try:
            # Seuils ajustés
            TECH_THRESHOLD = {TECH_THRESHOLD}
            COMP_THRESHOLD = {COMP_THRESHOLD}
            CONF_THRESHOLD = {CONF_THRESHOLD}
            
            # Validation des signaux
            validation = self._validate_adjusted_optimized_signals(
                technical_score, composite_score, confidence_level
            )
            
            # Filtrage ajusté : au moins 2 critères sur 3
            return validation["overall_valid"]
            
        except Exception as e:
            self.logger.warning(f"Erreur lors du filtrage ajusté: {{e}}")
            return False
'''
        
        return methods_code
    
    def implement_adjusted_thresholds(self):
        """Implémente les seuils ajustés"""
        print("🔧 Implémentation des seuils d'optimisation ajustés...")
        
        # Lire le fichier AdvancedTradingAnalysis
        try:
            with open(self.advanced_analysis_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"❌ Fichier {self.advanced_analysis_file} non trouvé")
            return False
        
        # Vérifier si les méthodes ajustées existent déjà
        if "_calculate_adjusted_optimized_composite_score" in content:
            print("⚠️ Les méthodes ajustées existent déjà")
            return True
        
        # Générer le code des méthodes ajustées
        adjusted_methods = self.generate_adjusted_thresholds()
        
        # Trouver le point d'insertion (avant la méthode analyze_opportunity)
        insertion_point = "    async def analyze_opportunity"
        if insertion_point not in content:
            print("❌ Point d'insertion non trouvé")
            return False
        
        # Insérer les méthodes ajustées
        new_content = content.replace(
            insertion_point,
            adjusted_methods + "\n" + insertion_point
        )
        
        # Sauvegarder le fichier modifié
        try:
            with open(self.advanced_analysis_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("✅ Méthodes ajustées implémentées avec succès")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            return False
    
    def update_analyze_opportunity_method(self):
        """Met à jour la méthode analyze_opportunity pour utiliser les seuils ajustés"""
        print("🔄 Mise à jour de la méthode analyze_opportunity avec les seuils ajustés...")
        
        try:
            with open(self.advanced_analysis_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"❌ Fichier {self.advanced_analysis_file} non trouvé")
            return False
        
        # Remplacer les appels aux méthodes optimisées par les méthodes ajustées
        replacements = [
            ("_calculate_priority_optimized_composite_score", "_calculate_adjusted_optimized_composite_score"),
            ("_determine_priority_optimized_recommendation", "_determine_adjusted_optimized_recommendation"),
            ("_validate_priority_optimized_signals", "_validate_adjusted_optimized_signals"),
            ("_apply_priority_optimized_filtering", "_apply_adjusted_optimized_filtering")
        ]
        
        for old_method, new_method in replacements:
            if old_method in content:
                content = content.replace(old_method, new_method)
                print(f"✅ {old_method} remplacé par {new_method}")
            else:
                print(f"⚠️ {old_method} non trouvé")
        
        # Sauvegarder le fichier modifié
        try:
            with open(self.advanced_analysis_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ Méthode analyze_opportunity mise à jour")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            return False
    
    def run_adjustment(self):
        """Exécute l'ajustement complet"""
        print("🚀 Démarrage de l'ajustement des seuils d'optimisation")
        print("=" * 80)
        
        # Implémenter les méthodes ajustées
        if not self.implement_adjusted_thresholds():
            return False
        
        # Mettre à jour la méthode analyze_opportunity
        if not self.update_analyze_opportunity_method():
            return False
        
        print("\n✅ Ajustement terminé avec succès")
        print("\n📊 RÉSUMÉ DES SEUILS AJUSTÉS:")
        print("  • Seuil technique: 0.45 (réduit de 0.533)")
        print("  • Seuil composite: 0.50 (réduit de 0.651)")
        print("  • Seuil confiance: 0.6 (maintenu)")
        print("  • Poids technique: 80% (maintenu)")
        print("  • Validation: au moins 2 critères sur 3 (maintenu)")
        
        return True

def main():
    """Fonction principale"""
    adjuster = OptimizationThresholdsAdjuster()
    
    try:
        success = adjuster.run_adjustment()
        if success:
            print("\n🎯 Les seuils d'optimisation ont été ajustés avec succès!")
            print("   Les seuils sont maintenant plus réalistes et permettront de générer des opportunités.")
        else:
            print("\n❌ Échec de l'ajustement")
    
    except Exception as e:
        print(f"❌ Erreur lors de l'ajustement: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
