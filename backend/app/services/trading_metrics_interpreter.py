"""
Service d'interprétation des métriques de trading
================================================

Ce service fournit des interprétations intelligentes et des recommandations
basées sur les métriques calculées par le framework de comparaison.
"""

import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """Niveaux de risque pour les modèles"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"

class PerformanceGrade(Enum):
    """Notes de performance"""
    EXCELLENT = "A+"
    VERY_GOOD = "A"
    GOOD = "B"
    AVERAGE = "C"
    POOR = "D"
    FAILING = "F"

@dataclass
class MetricInterpretation:
    """Interprétation d'une métrique"""
    value: float
    grade: PerformanceGrade
    interpretation: str
    recommendation: str
    risk_level: RiskLevel
    color: str

@dataclass
class ModelAnalysis:
    """Analyse complète d'un modèle"""
    model_name: str
    overall_grade: PerformanceGrade
    risk_level: RiskLevel
    is_tradable: bool
    confidence_score: float
    key_strengths: List[str]
    key_weaknesses: List[str]
    recommendations: List[str]
    warnings: List[str]
    metrics_analysis: Dict[str, MetricInterpretation]

class TradingMetricsInterpreter:
    """Interprète les métriques de trading et fournit des recommandations"""
    
    def __init__(self):
        self.risk_thresholds = {
            'sharpe_ratio': {
                'excellent': 2.0,
                'good': 1.0,
                'acceptable': 0.5,
                'poor': 0.0,
                'critical': -1.0
            },
            'total_return': {
                'excellent': 0.20,  # 20%
                'good': 0.10,      # 10%
                'acceptable': 0.05, # 5%
                'poor': 0.0,       # 0%
                'critical': -0.05   # -5%
            },
            'max_drawdown': {
                'excellent': 0.05,  # 5%
                'good': 0.10,      # 10%
                'acceptable': 0.15, # 15%
                'poor': 0.25,      # 25%
                'critical': 0.50    # 50%
            },
            'win_rate': {
                'excellent': 0.70,  # 70%
                'good': 0.60,       # 60%
                'acceptable': 0.50, # 50%
                'poor': 0.40,      # 40%
                'critical': 0.30   # 30%
            },
            'profit_factor': {
                'excellent': 2.0,
                'good': 1.5,
                'acceptable': 1.2,
                'poor': 1.0,
                'critical': 0.8
            },
            'accuracy': {
                'excellent': 0.80,  # 80%
                'good': 0.70,       # 70%
                'acceptable': 0.60, # 60%
                'poor': 0.50,       # 50%
                'critical': 0.40    # 40%
            },
            'f1_score': {
                'excellent': 0.80,  # 80%
                'good': 0.70,       # 70%
                'acceptable': 0.60, # 60%
                'poor': 0.50,       # 50%
                'critical': 0.40     # 40%
            }
        }
    
    def interpret_sharpe_ratio(self, sharpe: float) -> MetricInterpretation:
        """Interprète le Sharpe Ratio"""
        if sharpe >= 2.0:
            grade = PerformanceGrade.EXCELLENT
            interpretation = f"Sharpe Ratio exceptionnel ({sharpe:.3f}). Le modèle génère un rendement excédentaire très élevé par rapport au risque pris."
            recommendation = "Modèle recommandé pour un portefeuille agressif. Excellent équilibre rendement/risque."
            risk_level = RiskLevel.VERY_LOW
            color = "text-green-600"
        elif sharpe >= 1.0:
            grade = PerformanceGrade.VERY_GOOD
            interpretation = f"Sharpe Ratio très bon ({sharpe:.3f}). Bon équilibre entre rendement et risque."
            recommendation = "Modèle recommandé pour la plupart des stratégies. Performance solide."
            risk_level = RiskLevel.LOW
            color = "text-green-500"
        elif sharpe >= 0.5:
            grade = PerformanceGrade.GOOD
            interpretation = f"Sharpe Ratio acceptable ({sharpe:.3f}). Rendement modéré pour le risque pris."
            recommendation = "Modèle utilisable avec prudence. Surveiller les performances."
            risk_level = RiskLevel.MEDIUM
            color = "text-yellow-500"
        elif sharpe >= 0.0:
            grade = PerformanceGrade.AVERAGE
            interpretation = f"Sharpe Ratio faible ({sharpe:.3f}). Rendement insuffisant pour le risque."
            recommendation = "Modèle non recommandé. Considérer des améliorations avant utilisation."
            risk_level = RiskLevel.HIGH
            color = "text-orange-500"
        else:
            grade = PerformanceGrade.FAILING
            interpretation = f"Sharpe Ratio négatif ({sharpe:.3f}). Le modèle génère des pertes par rapport au risque pris."
            recommendation = "⚠️ ATTENTION: Ce modèle fait perdre de l'argent. Ne pas utiliser pour du trading réel."
            risk_level = RiskLevel.CRITICAL
            color = "text-red-600"
        
        return MetricInterpretation(
            value=sharpe,
            grade=grade,
            interpretation=interpretation,
            recommendation=recommendation,
            risk_level=risk_level,
            color=color
        )
    
    def interpret_total_return(self, return_pct: float) -> MetricInterpretation:
        """Interprète le rendement total"""
        if return_pct >= 0.20:
            grade = PerformanceGrade.EXCELLENT
            interpretation = f"Rendement exceptionnel ({return_pct:.1%}). Le modèle génère des profits très élevés."
            recommendation = "Excellent modèle pour la croissance du capital. Surveiller la volatilité."
            risk_level = RiskLevel.LOW
            color = "text-green-600"
        elif return_pct >= 0.10:
            grade = PerformanceGrade.VERY_GOOD
            interpretation = f"Rendement très bon ({return_pct:.1%}). Performance solide et rentable."
            recommendation = "Modèle recommandé pour la plupart des objectifs d'investissement."
            risk_level = RiskLevel.LOW
            color = "text-green-500"
        elif return_pct >= 0.05:
            grade = PerformanceGrade.GOOD
            interpretation = f"Rendement acceptable ({return_pct:.1%}). Performance modérée mais positive."
            recommendation = "Modèle utilisable avec des attentes réalistes. Bon pour la préservation du capital."
            risk_level = RiskLevel.MEDIUM
            color = "text-yellow-500"
        elif return_pct >= 0.0:
            grade = PerformanceGrade.AVERAGE
            interpretation = f"Rendement faible ({return_pct:.1%}). Performance insuffisante."
            recommendation = "Modèle non recommandé. Considérer des améliorations ou des alternatives."
            risk_level = RiskLevel.HIGH
            color = "text-orange-500"
        else:
            grade = PerformanceGrade.FAILING
            interpretation = f"Rendement négatif ({return_pct:.1%}). Le modèle fait perdre de l'argent."
            recommendation = "🚨 DANGER: Ce modèle génère des pertes. Arrêter immédiatement toute utilisation."
            risk_level = RiskLevel.CRITICAL
            color = "text-red-600"
        
        return MetricInterpretation(
            value=return_pct,
            grade=grade,
            interpretation=interpretation,
            recommendation=recommendation,
            risk_level=risk_level,
            color=color
        )
    
    def interpret_max_drawdown(self, drawdown: float) -> MetricInterpretation:
        """Interprète le drawdown maximum"""
        if drawdown <= 0.05:
            grade = PerformanceGrade.EXCELLENT
            interpretation = f"Drawdown très faible ({drawdown:.1%}). Le modèle est très stable."
            recommendation = "Excellent pour les investisseurs conservateurs. Risque minimal."
            risk_level = RiskLevel.VERY_LOW
            color = "text-green-600"
        elif drawdown <= 0.10:
            grade = PerformanceGrade.VERY_GOOD
            interpretation = f"Drawdown faible ({drawdown:.1%}). Le modèle est relativement stable."
            recommendation = "Bon pour la plupart des profils de risque. Surveillance normale requise."
            risk_level = RiskLevel.LOW
            color = "text-green-500"
        elif drawdown <= 0.15:
            grade = PerformanceGrade.GOOD
            interpretation = f"Drawdown modéré ({drawdown:.1%}). Volatilité acceptable."
            recommendation = "Acceptable pour les investisseurs modérés. Surveiller les périodes de stress."
            risk_level = RiskLevel.MEDIUM
            color = "text-yellow-500"
        elif drawdown <= 0.25:
            grade = PerformanceGrade.AVERAGE
            interpretation = f"Drawdown élevé ({drawdown:.1%}). Le modèle est volatil."
            recommendation = "Réservé aux investisseurs agressifs. Risque de pertes importantes."
            risk_level = RiskLevel.HIGH
            color = "text-orange-500"
        else:
            grade = PerformanceGrade.FAILING
            interpretation = f"Drawdown critique ({drawdown:.1%}). Le modèle est extrêmement volatil."
            recommendation = "⚠️ RISQUE ÉLEVÉ: Perte de capital importante possible. Utilisation déconseillée."
            risk_level = RiskLevel.CRITICAL
            color = "text-red-600"
        
        return MetricInterpretation(
            value=drawdown,
            grade=grade,
            interpretation=interpretation,
            recommendation=recommendation,
            risk_level=risk_level,
            color=color
        )
    
    def interpret_win_rate(self, win_rate: float) -> MetricInterpretation:
        """Interprète le taux de réussite"""
        if win_rate >= 0.70:
            grade = PerformanceGrade.EXCELLENT
            interpretation = f"Taux de réussite exceptionnel ({win_rate:.1%}). Le modèle prédit correctement dans la plupart des cas."
            recommendation = "Modèle très fiable. Excellent pour la confiance des traders."
            risk_level = RiskLevel.VERY_LOW
            color = "text-green-600"
        elif win_rate >= 0.60:
            grade = PerformanceGrade.VERY_GOOD
            interpretation = f"Taux de réussite très bon ({win_rate:.1%}). Prédictions généralement correctes."
            recommendation = "Modèle fiable. Bon pour la plupart des stratégies."
            risk_level = RiskLevel.LOW
            color = "text-green-500"
        elif win_rate >= 0.50:
            grade = PerformanceGrade.GOOD
            interpretation = f"Taux de réussite acceptable ({win_rate:.1%}). Prédictions moyennement fiables."
            recommendation = "Modèle utilisable avec prudence. Surveiller la qualité des signaux."
            risk_level = RiskLevel.MEDIUM
            color = "text-yellow-500"
        elif win_rate >= 0.40:
            grade = PerformanceGrade.AVERAGE
            interpretation = f"Taux de réussite faible ({win_rate:.1%}). Prédictions peu fiables."
            recommendation = "Modèle non recommandé. Améliorer la précision avant utilisation."
            risk_level = RiskLevel.HIGH
            color = "text-orange-500"
        else:
            grade = PerformanceGrade.FAILING
            interpretation = f"Taux de réussite critique ({win_rate:.1%}). Le modèle prédit incorrectement la plupart du temps."
            recommendation = "🚨 DANGER: Ce modèle est contre-productif. Arrêter immédiatement."
            risk_level = RiskLevel.CRITICAL
            color = "text-red-600"
        
        return MetricInterpretation(
            value=win_rate,
            grade=grade,
            interpretation=interpretation,
            recommendation=recommendation,
            risk_level=risk_level,
            color=color
        )
    
    def interpret_accuracy(self, accuracy: float) -> MetricInterpretation:
        """Interprète l'accuracy du modèle ML"""
        if accuracy >= 0.80:
            grade = PerformanceGrade.EXCELLENT
            interpretation = f"Accuracy exceptionnelle ({accuracy:.1%}). Le modèle ML est très précis."
            recommendation = "Modèle ML très fiable. Excellent pour la prise de décision automatisée."
            risk_level = RiskLevel.VERY_LOW
            color = "text-green-600"
        elif accuracy >= 0.70:
            grade = PerformanceGrade.VERY_GOOD
            interpretation = f"Accuracy très bonne ({accuracy:.1%}). Le modèle ML est précis."
            recommendation = "Modèle ML fiable. Bon pour la plupart des applications."
            risk_level = RiskLevel.LOW
            color = "text-green-500"
        elif accuracy >= 0.60:
            grade = PerformanceGrade.GOOD
            interpretation = f"Accuracy acceptable ({accuracy:.1%}). Le modèle ML est moyennement précis."
            recommendation = "Modèle ML utilisable avec prudence. Surveiller les performances."
            risk_level = RiskLevel.MEDIUM
            color = "text-yellow-500"
        elif accuracy >= 0.50:
            grade = PerformanceGrade.AVERAGE
            interpretation = f"Accuracy faible ({accuracy:.1%}). Le modèle ML manque de précision."
            recommendation = "Modèle ML non recommandé. Améliorer l'entraînement avant utilisation."
            risk_level = RiskLevel.HIGH
            color = "text-orange-500"
        else:
            grade = PerformanceGrade.FAILING
            interpretation = f"Accuracy critique ({accuracy:.1%}). Le modèle ML est contre-productif."
            recommendation = "🚨 DANGER: Ce modèle ML fait plus de mal que de bien. Arrêter immédiatement."
            risk_level = RiskLevel.CRITICAL
            color = "text-red-600"
        
        return MetricInterpretation(
            value=accuracy,
            grade=grade,
            interpretation=interpretation,
            recommendation=recommendation,
            risk_level=risk_level,
            color=color
        )
    
    def analyze_model(self, model_name: str, metrics: Dict[str, Any]) -> ModelAnalysis:
        """Analyse complète d'un modèle basée sur toutes ses métriques"""
        
        # Nettoyer les métriques (remplacer None par 0)
        cleaned_metrics = {}
        for key, value in metrics.items():
            if value is None:
                cleaned_metrics[key] = 0.0
            else:
                cleaned_metrics[key] = value
        
        # Interpréter chaque métrique
        metrics_analysis = {}
        
        if 'sharpe_ratio' in cleaned_metrics:
            metrics_analysis['sharpe_ratio'] = self.interpret_sharpe_ratio(cleaned_metrics['sharpe_ratio'])
        
        if 'total_return' in cleaned_metrics:
            metrics_analysis['total_return'] = self.interpret_total_return(cleaned_metrics['total_return'])
        
        if 'max_drawdown' in cleaned_metrics:
            metrics_analysis['max_drawdown'] = self.interpret_max_drawdown(cleaned_metrics['max_drawdown'])
        
        if 'win_rate' in cleaned_metrics:
            metrics_analysis['win_rate'] = self.interpret_win_rate(cleaned_metrics['win_rate'])
        
        if 'accuracy' in cleaned_metrics:
            metrics_analysis['accuracy'] = self.interpret_accuracy(cleaned_metrics['accuracy'])
        
        # Calculer la note globale
        grades = [m.grade for m in metrics_analysis.values()]
        overall_grade = self._calculate_overall_grade(grades)
        
        # Déterminer le niveau de risque global
        risk_levels = [m.risk_level for m in metrics_analysis.values()]
        overall_risk = self._calculate_overall_risk(risk_levels)
        
        # Déterminer si le modèle est tradable
        is_tradable = self._is_model_tradable(metrics_analysis, overall_grade, overall_risk)
        
        # Calculer le score de confiance
        confidence_score = self._calculate_confidence_score(metrics_analysis)
        
        # Identifier les forces et faiblesses
        key_strengths = self._identify_strengths(metrics_analysis)
        key_weaknesses = self._identify_weaknesses(metrics_analysis)
        
        # Générer les recommandations
        recommendations = self._generate_recommendations(metrics_analysis, overall_grade, overall_risk)
        
        # Générer les avertissements
        warnings = self._generate_warnings(metrics_analysis, overall_risk)
        
        return ModelAnalysis(
            model_name=model_name,
            overall_grade=overall_grade,
            risk_level=overall_risk,
            is_tradable=is_tradable,
            confidence_score=confidence_score,
            key_strengths=key_strengths,
            key_weaknesses=key_weaknesses,
            recommendations=recommendations,
            warnings=warnings,
            metrics_analysis=metrics_analysis
        )
    
    def _calculate_overall_grade(self, grades: List[PerformanceGrade]) -> PerformanceGrade:
        """Calcule la note globale basée sur les notes individuelles"""
        if not grades:
            return PerformanceGrade.FAILING
        
        # Mapping des notes vers des valeurs numériques
        grade_values = {
            PerformanceGrade.EXCELLENT: 5,
            PerformanceGrade.VERY_GOOD: 4,
            PerformanceGrade.GOOD: 3,
            PerformanceGrade.AVERAGE: 2,
            PerformanceGrade.POOR: 1,
            PerformanceGrade.FAILING: 0
        }
        
        avg_value = sum(grade_values[grade] for grade in grades) / len(grades)
        
        if avg_value >= 4.5:
            return PerformanceGrade.EXCELLENT
        elif avg_value >= 3.5:
            return PerformanceGrade.VERY_GOOD
        elif avg_value >= 2.5:
            return PerformanceGrade.GOOD
        elif avg_value >= 1.5:
            return PerformanceGrade.AVERAGE
        elif avg_value >= 0.5:
            return PerformanceGrade.POOR
        else:
            return PerformanceGrade.FAILING
    
    def _calculate_overall_risk(self, risk_levels: List[RiskLevel]) -> RiskLevel:
        """Calcule le niveau de risque global"""
        if not risk_levels:
            return RiskLevel.CRITICAL
        
        # Prendre le niveau de risque le plus élevé
        risk_values = {
            RiskLevel.VERY_LOW: 1,
            RiskLevel.LOW: 2,
            RiskLevel.MEDIUM: 3,
            RiskLevel.HIGH: 4,
            RiskLevel.VERY_HIGH: 5,
            RiskLevel.CRITICAL: 6
        }
        
        max_risk_value = max(risk_values[risk] for risk in risk_levels)
        
        for risk, value in risk_values.items():
            if value == max_risk_value:
                return risk
    
    def _is_model_tradable(self, metrics_analysis: Dict[str, MetricInterpretation], 
                          overall_grade: PerformanceGrade, overall_risk: RiskLevel) -> bool:
        """Détermine si le modèle est utilisable pour du trading réel"""
        
        # Critères stricts pour la tradabilité
        if overall_risk == RiskLevel.CRITICAL:
            return False
        
        if overall_grade == PerformanceGrade.FAILING:
            return False
        
        # Vérifier les métriques critiques
        critical_metrics = ['sharpe_ratio', 'total_return']
        for metric_name in critical_metrics:
            if metric_name in metrics_analysis:
                metric = metrics_analysis[metric_name]
                if metric.risk_level == RiskLevel.CRITICAL:
                    return False
        
        return True
    
    def _calculate_confidence_score(self, metrics_analysis: Dict[str, MetricInterpretation]) -> float:
        """Calcule un score de confiance global (0-1)"""
        if not metrics_analysis:
            return 0.0
        
        # Poids des métriques
        weights = {
            'sharpe_ratio': 0.25,
            'total_return': 0.20,
            'max_drawdown': 0.15,
            'win_rate': 0.15,
            'accuracy': 0.15,
            'f1_score': 0.10
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for metric_name, metric in metrics_analysis.items():
            if metric_name in weights:
                weight = weights[metric_name]
                # Convertir la note en score (0-1)
                grade_scores = {
                    PerformanceGrade.EXCELLENT: 1.0,
                    PerformanceGrade.VERY_GOOD: 0.8,
                    PerformanceGrade.GOOD: 0.6,
                    PerformanceGrade.AVERAGE: 0.4,
                    PerformanceGrade.POOR: 0.2,
                    PerformanceGrade.FAILING: 0.0
                }
                
                score = grade_scores[metric.grade]
                total_score += score * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _identify_strengths(self, metrics_analysis: Dict[str, MetricInterpretation]) -> List[str]:
        """Identifie les forces du modèle"""
        strengths = []
        
        for metric_name, metric in metrics_analysis.items():
            if metric.grade in [PerformanceGrade.EXCELLENT, PerformanceGrade.VERY_GOOD]:
                if metric_name == 'sharpe_ratio':
                    strengths.append("Excellent équilibre rendement/risque")
                elif metric_name == 'total_return':
                    strengths.append("Rendements élevés et consistants")
                elif metric_name == 'max_drawdown':
                    strengths.append("Faible volatilité et stabilité")
                elif metric_name == 'win_rate':
                    strengths.append("Taux de réussite élevé")
                elif metric_name == 'accuracy':
                    strengths.append("Précision ML exceptionnelle")
        
        return strengths
    
    def _identify_weaknesses(self, metrics_analysis: Dict[str, MetricInterpretation]) -> List[str]:
        """Identifie les faiblesses du modèle"""
        weaknesses = []
        
        for metric_name, metric in metrics_analysis.items():
            if metric.grade in [PerformanceGrade.POOR, PerformanceGrade.FAILING]:
                if metric_name == 'sharpe_ratio':
                    weaknesses.append("Mauvais équilibre rendement/risque")
                elif metric_name == 'total_return':
                    weaknesses.append("Rendements insuffisants ou négatifs")
                elif metric_name == 'max_drawdown':
                    weaknesses.append("Volatilité excessive")
                elif metric_name == 'win_rate':
                    weaknesses.append("Taux de réussite faible")
                elif metric_name == 'accuracy':
                    weaknesses.append("Précision ML insuffisante")
        
        return weaknesses
    
    def _generate_recommendations(self, metrics_analysis: Dict[str, MetricInterpretation], 
                                overall_grade: PerformanceGrade, overall_risk: RiskLevel) -> List[str]:
        """Génère des recommandations spécifiques"""
        recommendations = []
        
        # Recommandations basées sur la note globale
        if overall_grade == PerformanceGrade.EXCELLENT:
            recommendations.append("✅ Modèle recommandé pour un usage intensif")
            recommendations.append("💡 Considérer pour l'automatisation complète")
        elif overall_grade == PerformanceGrade.VERY_GOOD:
            recommendations.append("✅ Modèle recommandé pour la plupart des stratégies")
            recommendations.append("📊 Surveiller les performances régulièrement")
        elif overall_grade == PerformanceGrade.GOOD:
            recommendations.append("⚠️ Modèle utilisable avec prudence")
            recommendations.append("🔍 Surveiller attentivement les métriques")
        elif overall_grade == PerformanceGrade.AVERAGE:
            recommendations.append("❌ Modèle non recommandé pour le trading réel")
            recommendations.append("🛠️ Améliorer avant utilisation")
        else:
            recommendations.append("🚨 ARRÊTER immédiatement l'utilisation")
            recommendations.append("🔧 Refonte complète nécessaire")
        
        # Recommandations spécifiques par métrique
        for metric_name, metric in metrics_analysis.items():
            if metric.risk_level == RiskLevel.CRITICAL:
                if metric_name == 'sharpe_ratio':
                    recommendations.append("🎯 Réviser complètement la logique de trading")
                elif metric_name == 'total_return':
                    recommendations.append("💰 Arrêter immédiatement - pertes importantes")
                elif metric_name == 'max_drawdown':
                    recommendations.append("📉 Implémenter des stop-loss stricts")
        
        return recommendations
    
    def _generate_warnings(self, metrics_analysis: Dict[str, MetricInterpretation], 
                         overall_risk: RiskLevel) -> List[str]:
        """Génère des avertissements de sécurité"""
        warnings = []
        
        if overall_risk == RiskLevel.CRITICAL:
            warnings.append("🚨 ALERTE CRITIQUE: Ce modèle présente un risque extrême")
            warnings.append("⚠️ Ne pas utiliser pour du trading réel")
        
        # Avertissements spécifiques
        for metric_name, metric in metrics_analysis.items():
            if metric.risk_level == RiskLevel.CRITICAL:
                if metric_name == 'sharpe_ratio':
                    warnings.append("⚠️ Sharpe Ratio négatif - le modèle fait perdre de l'argent")
                elif metric_name == 'total_return':
                    warnings.append("⚠️ Rendement négatif - perte de capital confirmée")
                elif metric_name == 'max_drawdown':
                    warnings.append("⚠️ Drawdown critique - risque de perte majeure")
        
        return warnings
