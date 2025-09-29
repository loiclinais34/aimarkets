#!/usr/bin/env python3
"""
Script pour implémenter les 3 recommandations prioritaires :
1. Utiliser les seuils optimisés pour la génération d'opportunités
2. Prioriser le score technique dans la formule de scoring
3. Appliquer la validation des signaux optimisés
"""

import sys
import os
from typing import Dict, Any
import json

# Ajouter le chemin du backend au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class PriorityRecommendationsImplementer:
    """Implémenteur des recommandations prioritaires"""
    
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
    
    def generate_optimized_methods(self, results: Dict[str, Any]) -> str:
        """Génère les méthodes optimisées avec les 3 recommandations prioritaires"""
        
        # Seuils optimaux basés sur l'analyse
        TECH_THRESHOLD = 0.533
        COMP_THRESHOLD = 0.651
        CONF_THRESHOLD = 0.6
        
        # Poids optimaux - priorité au score technique
        TECH_WEIGHT = 0.8
        SENTIMENT_WEIGHT = 0.1
        MARKET_WEIGHT = 0.1
        
        methods_code = f'''
    def _calculate_priority_optimized_composite_score(
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
        Recommandation 2: Prioriser le score technique dans la formule de scoring
        """
        try:
            # Poids optimisés - priorité forte au score technique
            priority_weights = {{
                'technical': {TECH_WEIGHT},      # 80% - priorité maximale
                'sentiment': {SENTIMENT_WEIGHT},  # 10%
                'market': {MARKET_WEIGHT}         # 10%
            }}
            
            # Score composite avec priorité technique
            composite_score = (
                priority_weights['technical'] * technical_score +
                priority_weights['sentiment'] * sentiment_score +
                priority_weights['market'] * market_score
            )
            
            return round(composite_score, 4)
            
        except Exception as e:
            self.logger.error(f"Error calculating priority optimized composite score: {{e}}")
            return 0.5
    
    def _determine_priority_optimized_recommendation(
        self, 
        composite_score: float, 
        technical_score: float,
        confidence_level: float
    ) -> str:
        """
        Détermine la recommandation avec les seuils optimisés
        Recommandation 1: Utiliser les seuils optimisés pour la génération d'opportunités
        """
        try:
            # Seuils optimaux basés sur l'analyse de performance
            TECH_THRESHOLD = {TECH_THRESHOLD}
            COMP_THRESHOLD = {COMP_THRESHOLD}
            CONF_THRESHOLD = {CONF_THRESHOLD}
            
            # Validation des seuils optimaux
            tech_valid = technical_score >= TECH_THRESHOLD
            comp_valid = composite_score >= COMP_THRESHOLD
            conf_valid = confidence_level >= CONF_THRESHOLD
            
            # Logique de recommandation avec seuils optimisés
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
            self.logger.error(f"Error determining priority optimized recommendation: {{e}}")
            return "HOLD"
    
    def _validate_priority_optimized_signals(
        self, 
        technical_score: float, 
        composite_score: float,
        confidence_level: float
    ) -> Dict[str, bool]:
        """
        Valide les signaux avec les seuils optimisés
        Recommandation 3: Appliquer la validation des signaux optimisés
        """
        validation = {{
            "technical_threshold_met": False,
            "composite_threshold_met": False,
            "confidence_threshold_met": False,
            "overall_valid": False
        }}
        
        try:
            # Seuils optimaux
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
            self.logger.warning(f"Erreur lors de la validation optimisée: {{e}}")
        
        return validation
    
    def _apply_priority_optimized_filtering(
        self, 
        technical_score: float, 
        composite_score: float,
        confidence_level: float
    ) -> bool:
        """
        Applique le filtrage optimisé pour ne garder que les opportunités de haute qualité
        Combine les 3 recommandations prioritaires
        """
        try:
            # Seuils optimaux
            TECH_THRESHOLD = {TECH_THRESHOLD}
            COMP_THRESHOLD = {COMP_THRESHOLD}
            CONF_THRESHOLD = {CONF_THRESHOLD}
            
            # Validation des signaux
            validation = self._validate_priority_optimized_signals(
                technical_score, composite_score, confidence_level
            )
            
            # Filtrage strict : au moins 2 critères sur 3
            return validation["overall_valid"]
            
        except Exception as e:
            self.logger.warning(f"Erreur lors du filtrage optimisé: {{e}}")
            return False
'''
        
        return methods_code
    
    def implement_priority_recommendations(self):
        """Implémente les 3 recommandations prioritaires"""
        print("🚀 Implémentation des 3 recommandations prioritaires...")
        
        # Charger les résultats d'optimisation
        results = self.load_optimization_results()
        if not results:
            print("❌ Impossible de charger les résultats d'optimisation")
            return False
        
        # Générer le code des méthodes optimisées
        optimized_methods = self.generate_optimized_methods(results)
        
        # Lire le fichier AdvancedTradingAnalysis
        try:
            with open(self.advanced_analysis_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"❌ Fichier {self.advanced_analysis_file} non trouvé")
            return False
        
        # Vérifier si les méthodes prioritaires existent déjà
        if "_calculate_priority_optimized_composite_score" in content:
            print("⚠️ Les méthodes prioritaires existent déjà")
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
            print("✅ Méthodes prioritaires implémentées avec succès")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            return False
    
    def update_analyze_opportunity_method(self):
        """Met à jour la méthode analyze_opportunity pour utiliser les recommandations prioritaires"""
        print("🔄 Mise à jour de la méthode analyze_opportunity...")
        
        try:
            with open(self.advanced_analysis_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"❌ Fichier {self.advanced_analysis_file} non trouvé")
            return False
        
        # Remplacer l'appel au score composite
        old_composite_call = "composite_score = self._calculate_optimized_composite_score("
        new_composite_call = "composite_score = self._calculate_priority_optimized_composite_score("
        
        if old_composite_call in content:
            content = content.replace(old_composite_call, new_composite_call)
            print("✅ Appel au score composite prioritaire")
        else:
            print("⚠️ Appel au score composite non trouvé")
        
        # Remplacer l'appel à la recommandation
        old_rec_call = "recommendation, risk_level = self._determine_recommendation("
        new_rec_call = "recommendation = self._determine_priority_optimized_recommendation("
        
        if old_rec_call in content:
            content = content.replace(old_rec_call, new_rec_call)
            print("✅ Appel à la recommandation prioritaire")
        else:
            print("⚠️ Appel à la recommandation non trouvé")
        
        # Ajouter la validation des signaux optimisés
        validation_insertion = '''
            # Validation des signaux optimisés (Recommandation 3)
            signal_validation = self._validate_priority_optimized_signals(
                technical_score, composite_score, confidence_level
            )
            
            # Filtrage optimisé - ne garder que les opportunités de haute qualité
            if not self._apply_priority_optimized_filtering(
                technical_score, composite_score, confidence_level
            ):
                # Si le signal ne passe pas le filtrage, retourner HOLD
                recommendation = "HOLD"
            
            # Détermination du niveau de risque basé sur la validation
            if signal_validation["overall_valid"]:
                if confidence_level >= 0.8:
                    risk_level = "LOW"
                elif confidence_level >= 0.6:
                    risk_level = "MEDIUM"
                else:
                    risk_level = "HIGH"
            else:
                risk_level = "HIGH"
'''
        
        # Insérer la validation après le calcul de la recommandation
        recommendation_line = "recommendation = self._determine_priority_optimized_recommendation("
        if recommendation_line in content:
            # Trouver la fin de la ligne de recommandation
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if recommendation_line in line:
                    # Insérer la validation après cette ligne
                    lines.insert(i + 1, validation_insertion)
                    break
            content = '\n'.join(lines)
            print("✅ Validation des signaux optimisés ajoutée")
        else:
            print("⚠️ Ligne de recommandation non trouvée pour l'insertion")
        
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
        """Exécute l'implémentation complète des recommandations prioritaires"""
        print("🚀 Démarrage de l'implémentation des recommandations prioritaires")
        print("=" * 80)
        
        # Implémenter les méthodes prioritaires
        if not self.implement_priority_recommendations():
            return False
        
        # Mettre à jour la méthode analyze_opportunity
        if not self.update_analyze_opportunity_method():
            return False
        
        print("\n✅ Implémentation terminée avec succès")
        print("\n📊 RÉSUMÉ DES RECOMMANDATIONS PRIORITAIRES IMPLÉMENTÉES:")
        print("  ✅ 1. Seuils optimisés pour la génération d'opportunités")
        print("     - Seuil technique: 0.533")
        print("     - Seuil composite: 0.651")
        print("     - Seuil confiance: 0.600")
        print("  ✅ 2. Priorité au score technique dans la formule de scoring")
        print("     - Poids technique: 80%")
        print("     - Poids sentiment: 10%")
        print("     - Poids marché: 10%")
        print("  ✅ 3. Validation des signaux optimisés")
        print("     - Filtrage strict: au moins 2 critères sur 3")
        print("     - Niveau de risque basé sur la validation")
        print("     - Rejet automatique des signaux de faible qualité")
        
        return True

def main():
    """Fonction principale"""
    implementer = PriorityRecommendationsImplementer()
    
    try:
        success = implementer.run_implementation()
        if success:
            print("\n🎯 Les 3 recommandations prioritaires ont été implémentées avec succès!")
            print("   Les opportunités générées utiliseront maintenant les seuils optimisés.")
        else:
            print("\n❌ Échec de l'implémentation")
    
    except Exception as e:
        print(f"❌ Erreur lors de l'implémentation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
