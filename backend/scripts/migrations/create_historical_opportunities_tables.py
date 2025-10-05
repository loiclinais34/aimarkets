#!/usr/bin/env python3
"""
Script pour créer les tables des opportunités historiques
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_historical_opportunities_tables():
    """Crée les tables pour les opportunités historiques"""
    
    # Créer l'engine de base de données
    engine = create_engine(settings.database_url)
    
    try:
        with engine.connect() as connection:
            # Créer la table historical_opportunities
            logger.info("Création de la table historical_opportunities...")
            
            create_historical_opportunities_sql = """
            CREATE TABLE IF NOT EXISTS historical_opportunities (
                id BIGSERIAL PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                opportunity_date DATE NOT NULL,
                generation_timestamp TIMESTAMP DEFAULT NOW() NOT NULL,
                
                -- Scores et recommandations
                technical_score NUMERIC(5,4),
                sentiment_score NUMERIC(5,4),
                market_score NUMERIC(5,4),
                ml_score NUMERIC(5,4),
                composite_score NUMERIC(5,4),
                
                recommendation VARCHAR(10),
                confidence_level VARCHAR(10),
                risk_level VARCHAR(10),
                
                -- Données contextuelles
                price_at_generation NUMERIC(10,4),
                volume_at_generation BIGINT,
                market_cap_at_generation BIGINT,
                
                -- Métriques de performance futures
                price_1_day_later NUMERIC(10,4),
                price_7_days_later NUMERIC(10,4),
                price_30_days_later NUMERIC(10,4),
                
                return_1_day NUMERIC(8,6),
                return_7_days NUMERIC(8,6),
                return_30_days NUMERIC(8,6),
                
                -- Validation des recommandations
                recommendation_correct_1_day BOOLEAN,
                recommendation_correct_7_days BOOLEAN,
                recommendation_correct_30_days BOOLEAN,
                
                -- Score de performance global
                performance_score NUMERIC(5,4),
                
                -- Données détaillées des indicateurs (JSON)
                technical_indicators_data JSONB,
                sentiment_indicators_data JSONB,
                market_indicators_data JSONB,
                ml_indicators_data JSONB,
                
                -- Métadonnées
                created_at TIMESTAMP DEFAULT NOW() NOT NULL,
                updated_at TIMESTAMP DEFAULT NOW() NOT NULL
            );
            """
            
            connection.execute(text(create_historical_opportunities_sql))
            connection.commit()
            
            # Créer les index
            logger.info("Création des index pour historical_opportunities...")
            
            indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_historical_opp_symbol ON historical_opportunities(symbol);",
                "CREATE INDEX IF NOT EXISTS idx_historical_opp_date ON historical_opportunities(opportunity_date);",
                "CREATE INDEX IF NOT EXISTS idx_historical_opp_symbol_date ON historical_opportunities(symbol, opportunity_date);",
                "CREATE INDEX IF NOT EXISTS idx_historical_opp_date_performance ON historical_opportunities(opportunity_date, performance_score);",
                "CREATE INDEX IF NOT EXISTS idx_historical_opp_recommendation ON historical_opportunities(recommendation, opportunity_date);",
                "CREATE INDEX IF NOT EXISTS idx_historical_opp_generation_timestamp ON historical_opportunities(generation_timestamp);"
            ]
            
            for index_sql in indexes_sql:
                connection.execute(text(index_sql))
            
            connection.commit()
            
            # Créer la table historical_opportunity_validation
            logger.info("Création de la table historical_opportunity_validation...")
            
            create_validation_sql = """
            CREATE TABLE IF NOT EXISTS historical_opportunity_validation (
                id BIGSERIAL PRIMARY KEY,
                historical_opportunity_id BIGINT NOT NULL,
                
                -- Paramètres de validation
                validation_period_days INTEGER NOT NULL,
                validation_date DATE NOT NULL,
                
                -- Résultats de validation
                actual_return NUMERIC(8,6),
                predicted_return NUMERIC(8,6),
                prediction_error NUMERIC(8,6),
                
                -- Métriques de performance
                sharpe_ratio NUMERIC(8,6),
                max_drawdown NUMERIC(8,6),
                volatility NUMERIC(8,6),
                
                -- Classification de la performance
                performance_category VARCHAR(20),
                
                -- Données de marché
                market_return NUMERIC(8,6),
                beta NUMERIC(8,6),
                
                -- Métadonnées
                created_at TIMESTAMP DEFAULT NOW() NOT NULL,
                updated_at TIMESTAMP DEFAULT NOW() NOT NULL
            );
            """
            
            connection.execute(text(create_validation_sql))
            connection.commit()
            
            # Créer les index pour la table de validation
            logger.info("Création des index pour historical_opportunity_validation...")
            
            validation_indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_validation_opp_id ON historical_opportunity_validation(historical_opportunity_id);",
                "CREATE INDEX IF NOT EXISTS idx_validation_period_date ON historical_opportunity_validation(validation_period_days, validation_date);",
                "CREATE INDEX IF NOT EXISTS idx_validation_performance ON historical_opportunity_validation(performance_category, validation_period_days);"
            ]
            
            for index_sql in validation_indexes_sql:
                connection.execute(text(index_sql))
            
            connection.commit()
            
            logger.info("✅ Tables créées avec succès!")
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création des tables: {e}")
        raise


if __name__ == "__main__":
    create_historical_opportunities_tables()
