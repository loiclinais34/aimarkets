#!/usr/bin/env python3
"""
Script d'ingestion des données AIMarkets
Permet d'importer les données CSV dans la base de données PostgreSQL
"""

import os
import sys
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Ajouter le répertoire parent au path pour importer les modules
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.models.database import HistoricalData, SentimentData


class DataIngestion:
    def __init__(self):
        self.engine = create_engine(settings.database_url)
        self.Session = sessionmaker(bind=self.engine)
    
    def ingest_historical_data(self, csv_path: str, batch_size: int = 1000):
        """Ingérer les données historiques depuis un fichier CSV"""
        if not os.path.exists(csv_path):
            print(f"❌ Le fichier {csv_path} n'existe pas")
            return False
        
        try:
            print(f"🔄 Lecture du fichier {csv_path}...")
            
            # Lire le fichier CSV par chunks pour gérer les gros fichiers
            chunk_iter = pd.read_csv(csv_path, chunksize=batch_size)
            
            total_records = 0
            session = self.Session()
            
            try:
                for chunk_num, chunk in enumerate(chunk_iter):
                    print(f"📊 Traitement du chunk {chunk_num + 1}...")
                    
                    # Nettoyer et préparer les données
                    chunk = chunk.dropna(subset=['symbol', 'date', 'open', 'high', 'low', 'close', 'volume'])
                    
                    # Convertir les types de données
                    chunk['date'] = pd.to_datetime(chunk['date']).dt.date
                    chunk['open'] = pd.to_numeric(chunk['open'], errors='coerce')
                    chunk['high'] = pd.to_numeric(chunk['high'], errors='coerce')
                    chunk['low'] = pd.to_numeric(chunk['low'], errors='coerce')
                    chunk['close'] = pd.to_numeric(chunk['close'], errors='coerce')
                    chunk['volume'] = pd.to_numeric(chunk['volume'], errors='coerce')
                    chunk['vwap'] = pd.to_numeric(chunk['vwap'], errors='coerce')
                    
                    # Supprimer les lignes avec des valeurs manquantes
                    chunk = chunk.dropna()
                    
                    # Insérer les données
                    for _, row in chunk.iterrows():
                        try:
                            # Vérifier si l'enregistrement existe déjà
                            existing = session.query(HistoricalData).filter(
                                HistoricalData.symbol == row['symbol'],
                                HistoricalData.date == row['date']
                            ).first()
                            
                            if not existing:
                                historical_data = HistoricalData(
                                    symbol=row['symbol'],
                                    date=row['date'],
                                    open=row['open'],
                                    high=row['high'],
                                    low=row['low'],
                                    close=row['close'],
                                    volume=int(row['volume']),
                                    vwap=row['vwap'] if pd.notna(row['vwap']) else None
                                )
                                session.add(historical_data)
                                total_records += 1
                        except Exception as e:
                            print(f"⚠️ Erreur lors de l'insertion de {row['symbol']} - {row['date']}: {e}")
                            continue
                    
                    # Commit par batch
                    session.commit()
                    print(f"✅ Chunk {chunk_num + 1} traité: {len(chunk)} enregistrements")
                
                print(f"✅ Ingestion terminée: {total_records} nouveaux enregistrements")
                return True
                
            except Exception as e:
                session.rollback()
                print(f"❌ Erreur lors de l'ingestion: {e}")
                return False
            finally:
                session.close()
                
        except Exception as e:
            print(f"❌ Erreur lors de la lecture du fichier: {e}")
            return False
    
    def ingest_sentiment_data(self, csv_path: str, batch_size: int = 1000):
        """Ingérer les données de sentiment depuis un fichier CSV"""
        if not os.path.exists(csv_path):
            print(f"❌ Le fichier {csv_path} n'existe pas")
            return False
        
        try:
            print(f"🔄 Lecture du fichier {csv_path}...")
            
            # Lire le fichier CSV par chunks
            chunk_iter = pd.read_csv(csv_path, chunksize=batch_size)
            
            total_records = 0
            session = self.Session()
            
            try:
                for chunk_num, chunk in enumerate(chunk_iter):
                    print(f"📊 Traitement du chunk {chunk_num + 1}...")
                    
                    # Nettoyer et préparer les données
                    chunk = chunk.dropna(subset=['symbol', 'date'])
                    
                    # Convertir les types de données
                    chunk['date'] = pd.to_datetime(chunk['date']).dt.date
                    
                    # Convertir les colonnes numériques
                    numeric_columns = [
                        'news_count', 'news_sentiment_score', 'news_sentiment_std',
                        'news_positive_count', 'news_negative_count', 'news_neutral_count',
                        'top_news_sentiment', 'short_interest_ratio', 'short_interest_volume',
                        'short_volume', 'short_exempt_volume', 'total_volume',
                        'short_volume_ratio', 'sentiment_momentum_5d', 'sentiment_momentum_20d',
                        'sentiment_volatility_5d', 'sentiment_relative_strength', 'data_quality_score'
                    ]
                    
                    for col in numeric_columns:
                        if col in chunk.columns:
                            chunk[col] = pd.to_numeric(chunk[col], errors='coerce')
                    
                    # Convertir les colonnes de date
                    date_columns = ['short_interest_date']
                    for col in date_columns:
                        if col in chunk.columns:
                            chunk[col] = pd.to_datetime(chunk[col], errors='coerce').dt.date
                    
                    # Insérer les données
                    for _, row in chunk.iterrows():
                        try:
                            # Vérifier si l'enregistrement existe déjà
                            existing = session.query(SentimentData).filter(
                                SentimentData.symbol == row['symbol'],
                                SentimentData.date == row['date']
                            ).first()
                            
                            if not existing:
                                sentiment_data = SentimentData(
                                    symbol=row['symbol'],
                                    date=row['date'],
                                    news_count=int(row.get('news_count', 0)) if pd.notna(row.get('news_count')) else 0,
                                    news_sentiment_score=row.get('news_sentiment_score', 0.0) if pd.notna(row.get('news_sentiment_score')) else 0.0,
                                    news_sentiment_std=row.get('news_sentiment_std', 0.0) if pd.notna(row.get('news_sentiment_std')) else 0.0,
                                    news_positive_count=int(row.get('news_positive_count', 0)) if pd.notna(row.get('news_positive_count')) else 0,
                                    news_negative_count=int(row.get('news_negative_count', 0)) if pd.notna(row.get('news_negative_count')) else 0,
                                    news_neutral_count=int(row.get('news_neutral_count', 0)) if pd.notna(row.get('news_neutral_count')) else 0,
                                    top_news_title=row.get('top_news_title') if pd.notna(row.get('top_news_title')) else None,
                                    top_news_sentiment=row.get('top_news_sentiment') if pd.notna(row.get('top_news_sentiment')) else None,
                                    top_news_url=row.get('top_news_url') if pd.notna(row.get('top_news_url')) else None,
                                    short_interest_ratio=row.get('short_interest_ratio') if pd.notna(row.get('short_interest_ratio')) else None,
                                    short_interest_volume=int(row.get('short_interest_volume')) if pd.notna(row.get('short_interest_volume')) else None,
                                    short_interest_date=row.get('short_interest_date') if pd.notna(row.get('short_interest_date')) else None,
                                    short_volume=int(row.get('short_volume')) if pd.notna(row.get('short_volume')) else None,
                                    short_exempt_volume=int(row.get('short_exempt_volume')) if pd.notna(row.get('short_exempt_volume')) else None,
                                    total_volume=int(row.get('total_volume')) if pd.notna(row.get('total_volume')) else None,
                                    short_volume_ratio=row.get('short_volume_ratio') if pd.notna(row.get('short_volume_ratio')) else None,
                                    sentiment_momentum_5d=row.get('sentiment_momentum_5d') if pd.notna(row.get('sentiment_momentum_5d')) else None,
                                    sentiment_momentum_20d=row.get('sentiment_momentum_20d') if pd.notna(row.get('sentiment_momentum_20d')) else None,
                                    sentiment_volatility_5d=row.get('sentiment_volatility_5d') if pd.notna(row.get('sentiment_volatility_5d')) else None,
                                    sentiment_relative_strength=row.get('sentiment_relative_strength') if pd.notna(row.get('sentiment_relative_strength')) else None,
                                    data_quality_score=row.get('data_quality_score', 0.5) if pd.notna(row.get('data_quality_score')) else 0.5,
                                    processing_notes=row.get('processing_notes') if pd.notna(row.get('processing_notes')) else None
                                )
                                session.add(sentiment_data)
                                total_records += 1
                        except Exception as e:
                            print(f"⚠️ Erreur lors de l'insertion de {row['symbol']} - {row['date']}: {e}")
                            continue
                    
                    # Commit par batch
                    session.commit()
                    print(f"✅ Chunk {chunk_num + 1} traité: {len(chunk)} enregistrements")
                
                print(f"✅ Ingestion terminée: {total_records} nouveaux enregistrements")
                return True
                
            except Exception as e:
                session.rollback()
                print(f"❌ Erreur lors de l'ingestion: {e}")
                return False
            finally:
                session.close()
                
        except Exception as e:
            print(f"❌ Erreur lors de la lecture du fichier: {e}")
            return False
    
    def show_data_stats(self):
        """Afficher les statistiques des données ingérées"""
        try:
            session = self.Session()
            
            # Statistiques des données historiques
            historical_count = session.query(HistoricalData).count()
            historical_symbols = session.query(HistoricalData.symbol).distinct().count()
            historical_dates = session.query(HistoricalData.date).distinct().count()
            
            # Statistiques des données de sentiment
            sentiment_count = session.query(SentimentData).count()
            sentiment_symbols = session.query(SentimentData.symbol).distinct().count()
            sentiment_dates = session.query(SentimentData.date).distinct().count()
            
            print("📊 Statistiques des données ingérées:")
            print(f"📈 Données historiques:")
            print(f"  - Total: {historical_count:,} enregistrements")
            print(f"  - Symboles: {historical_symbols}")
            print(f"  - Dates: {historical_dates}")
            print(f"📰 Données de sentiment:")
            print(f"  - Total: {sentiment_count:,} enregistrements")
            print(f"  - Symboles: {sentiment_symbols}")
            print(f"  - Dates: {sentiment_dates}")
            
            session.close()
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des statistiques: {e}")


def main():
    parser = argparse.ArgumentParser(description="Script d'ingestion des données AIMarkets")
    parser.add_argument('action', choices=['ingest-historical', 'ingest-sentiment', 'ingest-all', 'stats'], 
                       help="Action à effectuer")
    parser.add_argument('--csv-path', help="Chemin vers le fichier CSV")
    parser.add_argument('--batch-size', type=int, default=1000, help="Taille des batches (défaut: 1000)")
    
    args = parser.parse_args()
    
    ingestion = DataIngestion()
    
    if args.action == 'ingest-historical':
        if not args.csv_path:
            args.csv_path = settings.data_historical_path
        ingestion.ingest_historical_data(args.csv_path, args.batch_size)
    elif args.action == 'ingest-sentiment':
        if not args.csv_path:
            args.csv_path = settings.data_sentiment_path
        ingestion.ingest_sentiment_data(args.csv_path, args.batch_size)
    elif args.action == 'ingest-all':
        print("🔄 Ingestion de toutes les données...")
        historical_success = ingestion.ingest_historical_data(settings.data_historical_path, args.batch_size)
        sentiment_success = ingestion.ingest_sentiment_data(settings.data_sentiment_path, args.batch_size)
        
        if historical_success and sentiment_success:
            print("✅ Toutes les données ont été ingérées avec succès")
        else:
            print("❌ Certaines données n'ont pas pu être ingérées")
    elif args.action == 'stats':
        ingestion.show_data_stats()


if __name__ == "__main__":
    main()
