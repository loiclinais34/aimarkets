#!/usr/bin/env python3
"""
Intégration des seuils optimisés dans la génération d'opportunités ML
Vide la table ml_opportunities_xgboost et la repeuple avec les seuils optimisés
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json
import sys
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

# Ajouter le chemin du backend
backend_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(backend_path)

from app.core.config import settings
from app.models.ml_opportunities_xgboost import MLOpportunityXGBoost

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class OptimizedThresholdConfig:
    """Configuration des seuils optimisés basée sur les résultats de la Phase 1"""
    # Configuration optimale par Sharpe Ratio (14.13)
    rsi_oversold_strong: float = 25
    rsi_oversold_weak: float = 35
    rsi_overbought_weak: float = 65
    rsi_overbought_strong: float = 70
    
    # Seuils MACD
    macd_bullish: float = 0
    macd_bearish: float = 0
    
    # Seuils Bollinger Bands Position
    bb_oversold: float = 0.1
    bb_overbought: float = 0.7
    
    # Seuils ADX (force de tendance)
    adx_min_strength: float = 20
    
    # Confiance et retours potentiels optimisés
    confidence_strong: float = 0.8
    confidence_weak: float = 0.7
    confidence_hold: float = 0.6
    
    return_strong: float = 0.03
    return_weak: float = 0.02
    return_hold: float = 0.01

class OptimizedOpportunityGenerator:
    """Générateur d'opportunités avec les seuils optimisés"""
    
    def __init__(self):
        DATABASE_URL = settings.database_url
        self.engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = SessionLocal()
        
        # Configuration optimisée
        self.config = OptimizedThresholdConfig()
        
        # Statistiques
        self.stats = {
            'total_generated': 0,
            'by_recommendation': {},
            'by_horizon': {},
            'by_symbol': {},
            'start_time': None,
            'end_time': None
        }
        
    def clear_xgboost_table(self):
        """Vide complètement la table ml_opportunities_xgboost"""
        logger.info("🗑️ Vidage de la table ml_opportunities_xgboost...")
        
        try:
            # Compter les enregistrements avant suppression
            count_query = "SELECT COUNT(*) FROM ml_opportunities_xgboost"
            old_count = self.db.execute(text(count_query)).scalar()
            logger.info(f"   📊 {old_count:,} enregistrements à supprimer")
            
            # Supprimer tous les enregistrements
            delete_query = "DELETE FROM ml_opportunities_xgboost"
            result = self.db.execute(text(delete_query))
            self.db.commit()
            
            logger.info(f"✅ Table vidée avec succès ({result.rowcount:,} enregistrements supprimés)")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du vidage de la table: {e}")
            self.db.rollback()
            raise
    
    def generate_optimized_recommendation(self, row: pd.Series) -> Tuple[str, float, float]:
        """
        Génère une recommandation optimisée basée sur les seuils de la Phase 1
        
        Args:
            row: Ligne de données avec les indicateurs techniques
            
        Returns:
            Tuple[recommendation, confidence, potential_return]
        """
        rsi = row.get('rsi_14', 50)
        macd = row.get('macd', 0)
        bb_position = row.get('bb_position', 0.5)
        adx = row.get('adx_14', 20)
        
        # Logique de recommandation avec seuils optimisés
        recommendation = "HOLD"
        confidence = self.config.confidence_hold
        potential_return = self.config.return_hold
        
        # BUY_STRONG : RSI très bas + MACD positif + BB très bas + ADX fort
        if (rsi < self.config.rsi_oversold_strong and 
            macd > self.config.macd_bullish and 
            bb_position < self.config.bb_oversold and
            adx > self.config.adx_min_strength):
            recommendation = "BUY_STRONG"
            confidence = self.config.confidence_strong
            potential_return = self.config.return_strong
            
        # BUY_WEAK : RSI bas + MACD positif
        elif (rsi < self.config.rsi_oversold_weak and 
              macd > self.config.macd_bullish):
            recommendation = "BUY_WEAK"
            confidence = self.config.confidence_weak
            potential_return = self.config.return_weak
            
        # SELL_STRONG : RSI très haut + MACD négatif + BB très haut + ADX fort
        elif (rsi > self.config.rsi_overbought_strong and 
              macd < self.config.macd_bearish and 
              bb_position > self.config.bb_overbought and
              adx > self.config.adx_min_strength):
            recommendation = "SELL_STRONG"
            confidence = self.config.confidence_strong
            potential_return = -self.config.return_strong
            
        # SELL_WEAK : RSI haut + MACD négatif
        elif (rsi > self.config.rsi_overbought_weak and 
              macd < self.config.macd_bearish):
            recommendation = "SELL_WEAK"
            confidence = self.config.confidence_weak
            potential_return = -self.config.return_weak
        
        return recommendation, confidence, potential_return
    
    def get_available_symbols(self) -> List[str]:
        """Récupère la liste des symboles disponibles"""
        logger.info("📊 Récupération des symboles disponibles...")
        
        query = """
        SELECT DISTINCT symbol 
        FROM advanced_technical_indicators 
        WHERE rsi_14 IS NOT NULL 
            AND macd IS NOT NULL 
            AND bb_position IS NOT NULL
            AND adx_14 IS NOT NULL
        ORDER BY symbol
        """
        
        result = self.db.execute(text(query))
        symbols = [row[0] for row in result.fetchall()]
        
        logger.info(f"   ✅ {len(symbols)} symboles trouvés")
        return symbols
    
    def get_available_dates_for_symbol(self, symbol: str) -> List[datetime]:
        """Récupère les dates disponibles pour un symbole"""
        query = """
        SELECT DISTINCT date 
        FROM advanced_technical_indicators 
        WHERE symbol = :symbol
            AND rsi_14 IS NOT NULL 
            AND macd IS NOT NULL 
            AND bb_position IS NOT NULL
            AND adx_14 IS NOT NULL
        ORDER BY date
        """
        
        result = self.db.execute(text(query), {"symbol": symbol})
        dates = [row[0] for row in result.fetchall()]
        
        return dates
    
    def generate_opportunities_for_symbol(self, symbol: str, horizons: List[int] = [1, 7, 30]) -> List[Dict]:
        """
        Génère les opportunités optimisées pour un symbole donné
        
        Args:
            symbol: Symbole à traiter
            horizons: Liste des horizons en jours
            
        Returns:
            Liste des opportunités générées
        """
        logger.info(f"📊 Traitement de {symbol}")
        
        opportunities = []
        dates = self.get_available_dates_for_symbol(symbol)
        
        if not dates:
            logger.warning(f"   ⚠️ Aucune date disponible pour {symbol}")
            return opportunities
        
        logger.info(f"   📅 {len(dates)} dates disponibles")
        
        for horizon in horizons:
            logger.info(f"   📅 Horizon {horizon}d: {len(dates)} dates disponibles")
            
            for opp_date in dates:
                try:
                    # Vérifier qu'on peut calculer le retour pour cet horizon
                    future_date = opp_date + timedelta(days=horizon)
                    if future_date not in dates:
                        continue
                    
                    # Récupérer les données techniques pour cette date
                    query = f"""
                    SELECT ati.*, hd.open, hd.high, hd.low, hd.close, hd.volume
                    FROM advanced_technical_indicators ati
                    JOIN historical_data hd ON ati.symbol = hd.symbol AND ati.date = hd.date
                    WHERE ati.symbol = '{symbol}' 
                        AND ati.date = '{opp_date}'
                    ORDER BY ati.date DESC
                    LIMIT 1
                    """
                    
                    df = pd.read_sql(query, self.db.connection())
                    
                    if df.empty:
                        continue
                    
                    row = df.iloc[0]
                    
                    # Générer la recommandation optimisée
                    recommendation, confidence, potential_return = self.generate_optimized_recommendation(row)
                    
                    # Ajuster selon l'horizon
                    if horizon == 1:
                        potential_return *= 0.3
                    elif horizon == 7:
                        potential_return *= 0.7
                    # horizon == 30 garde le potentiel complet
                    
                    opportunity = {
                        'symbol': symbol,
                        'date': opp_date,
                        'horizon_days': horizon,
                        'recommendation': recommendation,
                        'confidence_level': float(confidence),
                        'potential_return': float(potential_return),
                        'risk_score': float(1 - confidence),
                        'ml_model_name': 'optimized_thresholds_v1',
                        'ml_model_version': '1.0',
                        'technical_indicators': json.dumps({
                            'rsi_14': float(row.get('rsi_14', 50)) if pd.notna(row.get('rsi_14', 50)) else 50,
                            'macd': float(row.get('macd', 0)) if pd.notna(row.get('macd', 0)) else 0,
                            'bb_position': float(row.get('bb_position', 0.5)) if pd.notna(row.get('bb_position', 0.5)) else 0.5,
                            'adx_14': float(row.get('adx_14', 20)) if pd.notna(row.get('adx_14', 20)) else 20,
                            'volume_sma_ratio': float(row.get('volume_sma_ratio', 1)) if pd.notna(row.get('volume_sma_ratio', 1)) else 1
                        }),
                        'ml_features': json.dumps({
                            'momentum_score': float(row.get('rsi_14', 50) / 100) if pd.notna(row.get('rsi_14', 50)) else 0.5,
                            'trend_score': float(row.get('macd', 0)) if pd.notna(row.get('macd', 0)) else 0,
                            'bb_signal': float(row.get('bb_position', 0.5)) if pd.notna(row.get('bb_position', 0.5)) else 0.5,
                            'optimized_thresholds': True
                        })
                    }
                    
                    opportunities.append(opportunity)
                    
                    # Mettre à jour les statistiques
                    self.stats['total_generated'] += 1
                    self.stats['by_recommendation'][recommendation] = self.stats['by_recommendation'].get(recommendation, 0) + 1
                    self.stats['by_horizon'][f"{horizon}d"] = self.stats['by_horizon'].get(f"{horizon}d", 0) + 1
                    self.stats['by_symbol'][symbol] = self.stats['by_symbol'].get(symbol, 0) + 1
                    
                    if self.stats['total_generated'] % 1000 == 0:
                        logger.info(f"    📦 {self.stats['total_generated']} opportunités générées...")
                
                except Exception as e:
                    logger.warning(f"    ⚠️ Erreur pour {symbol} le {opp_date}: {e}")
                    continue
        
        logger.info(f"✅ {symbol}: {len(opportunities)} opportunités générées")
        return opportunities
    
    def store_opportunities_batch(self, opportunities: List[Dict]):
        """Stocke un batch d'opportunités en base"""
        if not opportunities:
            return
        
        try:
            for opp_data in opportunities:
                opportunity_obj = MLOpportunityXGBoost(**opp_data)
                self.db.add(opportunity_obj)
            
            self.db.commit()
            logger.info(f"💾 {len(opportunities)} opportunités stockées")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du stockage: {e}")
            self.db.rollback()
            raise
    
    def generate_all_optimized_opportunities(self, horizons: List[int] = [1, 7, 30], batch_size: int = 1000):
        """
        Génère toutes les opportunités optimisées pour tous les symboles
        
        Args:
            horizons: Liste des horizons en jours
            batch_size: Taille des batches pour le stockage
        """
        logger.info("🚀 Début de la génération d'opportunités optimisées")
        self.stats['start_time'] = datetime.now()
        
        try:
            # Vider la table existante
            self.clear_xgboost_table()
            
            # Récupérer tous les symboles
            symbols = self.get_available_symbols()
            
            if not symbols:
                logger.error("❌ Aucun symbole disponible")
                return
            
            logger.info(f"📊 {len(symbols)} symboles à traiter")
            
            # Traiter chaque symbole
            all_opportunities = []
            
            for i, symbol in enumerate(symbols, 1):
                logger.info(f"\n📊 Traitement de {symbol} ({i}/{len(symbols)})")
                
                # Générer les opportunités pour ce symbole
                symbol_opportunities = self.generate_opportunities_for_symbol(symbol, horizons)
                all_opportunities.extend(symbol_opportunities)
                
                # Stocker par batch pour optimiser les performances
                if len(all_opportunities) >= batch_size:
                    self.store_opportunities_batch(all_opportunities)
                    all_opportunities = []
            
            # Stocker les opportunités restantes
            if all_opportunities:
                self.store_opportunities_batch(all_opportunities)
            
            self.stats['end_time'] = datetime.now()
            
            # Afficher les statistiques finales
            self.display_final_statistics()
            
            logger.info("\n🎉 Génération d'opportunités optimisées terminée avec succès!")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la génération: {e}", exc_info=True)
            self.db.rollback()
            raise
        finally:
            self.db.close()
    
    def display_final_statistics(self):
        """Affiche les statistiques finales de génération"""
        logger.info("\n📈 STATISTIQUES FINALES")
        logger.info("=" * 50)
        
        duration = self.stats['end_time'] - self.stats['start_time']
        logger.info(f"⏱️  Temps total: {duration}")
        logger.info(f"📊 Total opportunités générées: {self.stats['total_generated']:,}")
        
        logger.info(f"\n🎯 Par recommandation:")
        for rec, count in self.stats['by_recommendation'].items():
            percentage = (count / self.stats['total_generated']) * 100
            logger.info(f"   {rec}: {count:,} ({percentage:.1f}%)")
        
        logger.info(f"\n⏰ Par horizon:")
        for horizon, count in self.stats['by_horizon'].items():
            percentage = (count / self.stats['total_generated']) * 100
            logger.info(f"   {horizon}: {count:,} ({percentage:.1f}%)")
        
        logger.info(f"\n🏷️ Symboles traités: {len(self.stats['by_symbol'])}")
        
        # Configuration utilisée
        logger.info(f"\n⚙️ Configuration optimisée utilisée:")
        logger.info(f"   RSI Oversold Strong: {self.config.rsi_oversold_strong}")
        logger.info(f"   RSI Oversold Weak: {self.config.rsi_oversold_weak}")
        logger.info(f"   RSI Overbought Weak: {self.config.rsi_overbought_weak}")
        logger.info(f"   RSI Overbought Strong: {self.config.rsi_overbought_strong}")
        logger.info(f"   BB Oversold: {self.config.bb_oversold}")
        logger.info(f"   BB Overbought: {self.config.bb_overbought}")
        logger.info(f"   Confidence Strong: {self.config.confidence_strong}")
        logger.info(f"   Confidence Weak: {self.config.confidence_weak}")
        logger.info(f"   Return Strong: {self.config.return_strong}")
        logger.info(f"   Return Weak: {self.config.return_weak}")
    
    def verify_generation(self):
        """Vérifie que la génération s'est bien déroulée"""
        logger.info("🔍 Vérification de la génération...")
        
        try:
            # Compter les opportunités générées
            count_query = "SELECT COUNT(*) FROM ml_opportunities_xgboost"
            total_count = self.db.execute(text(count_query)).scalar()
            
            # Compter par recommandation
            rec_query = """
            SELECT recommendation, COUNT(*) as count 
            FROM ml_opportunities_xgboost 
            GROUP BY recommendation 
            ORDER BY count DESC
            """
            rec_result = self.db.execute(text(rec_query))
            rec_counts = {row[0]: row[1] for row in rec_result.fetchall()}
            
            # Compter par horizon
            horizon_query = """
            SELECT horizon_days, COUNT(*) as count 
            FROM ml_opportunities_xgboost 
            GROUP BY horizon_days 
            ORDER BY horizon_days
            """
            horizon_result = self.db.execute(text(horizon_query))
            horizon_counts = {row[0]: row[1] for row in horizon_result.fetchall()}
            
            logger.info(f"✅ Vérification terminée:")
            logger.info(f"   Total opportunités: {total_count:,}")
            logger.info(f"   Par recommandation: {rec_counts}")
            logger.info(f"   Par horizon: {horizon_counts}")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la vérification: {e}")

def main():
    """Fonction principale"""
    generator = OptimizedOpportunityGenerator()
    
    try:
        # Générer toutes les opportunités optimisées
        generator.generate_all_optimized_opportunities()
        
        # Vérifier la génération
        generator.verify_generation()
        
    except Exception as e:
        logger.error(f"❌ Erreur dans le processus principal: {e}")
        raise

if __name__ == "__main__":
    main()
