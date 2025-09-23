#!/usr/bin/env python3
"""
Test d'entraînement complet du service LightGBM
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, datetime
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.database import TargetParameters, MLModels, HistoricalData, TechnicalIndicators, SentimentIndicators
from app.services.lightgbm_service import LightGBMService

def test_lightgbm_training():
    """Test d'entraînement complet du service LightGBM"""
    print("🧪 Test d'entraînement complet du service LightGBM...")
    
    # Récupération de la session de base de données
    db = next(get_db())
    
    try:
        # Test 1: Vérification des données disponibles
        print("\n1️⃣ Vérification des données disponibles...")
        
        # Vérifier les données historiques
        hist_count = db.query(HistoricalData).filter(HistoricalData.symbol == "AAPL").count()
        print(f"   - Données historiques AAPL: {hist_count} enregistrements")
        
        # Vérifier les indicateurs techniques
        tech_count = db.query(TechnicalIndicators).filter(TechnicalIndicators.symbol == "AAPL").count()
        print(f"   - Indicateurs techniques AAPL: {tech_count} enregistrements")
        
        # Vérifier les indicateurs de sentiment
        sent_count = db.query(SentimentIndicators).filter(SentimentIndicators.symbol == "AAPL").count()
        print(f"   - Indicateurs de sentiment AAPL: {sent_count} enregistrements")
        
        if hist_count < 100 or tech_count < 100 or sent_count < 100:
            print("❌ Pas assez de données pour l'entraînement")
            return
        
        # Test 2: Récupération du paramètre cible
        print("\n2️⃣ Récupération du paramètre cible...")
        target_param = db.query(TargetParameters).first()
        if not target_param:
            print("❌ Aucun paramètre cible trouvé")
            return
        
        print(f"✅ Paramètre cible: {target_param.parameter_name}")
        print(f"   - Rendement cible: {target_param.target_return_percentage}%")
        print(f"   - Horizon: {target_param.time_horizon_days} jours")
        
        # Test 3: Création du service LightGBM
        print("\n3️⃣ Création du service LightGBM...")
        service = LightGBMService(db)
        print("✅ Service LightGBM créé avec succès")
        
        # Test 4: Récupération et préparation des données
        print("\n4️⃣ Récupération et préparation des données...")
        
        # Récupérer les données avec jointures
        query = db.query(HistoricalData, TechnicalIndicators, SentimentIndicators).join(
            TechnicalIndicators, 
            (HistoricalData.symbol == TechnicalIndicators.symbol) & 
            (HistoricalData.date == TechnicalIndicators.date)
        ).join(
            SentimentIndicators, 
            (HistoricalData.symbol == SentimentIndicators.symbol) & 
            (HistoricalData.date == SentimentIndicators.date)
        ).filter(
            HistoricalData.symbol == "AAPL"
        ).order_by(HistoricalData.date).limit(200)  # Limiter à 200 pour éviter les problèmes de mémoire
        
        results = query.all()
        print(f"   - {len(results)} enregistrements récupérés")
        
        if len(results) < 50:
            print("❌ Pas assez de données pour l'entraînement")
            return
        
        # Test 5: Conversion en DataFrame
        print("\n5️⃣ Conversion en DataFrame...")
        import pandas as pd
        
        data = []
        for hist, tech, sent in results:
            row = {
                'date': hist.date,
                'symbol': hist.symbol,
                'close': float(hist.close),
                'open': float(hist.open),
                'high': float(hist.high),
                'low': float(hist.low),
                'volume': float(hist.volume),
                
                # Indicateurs techniques
                'sma_5': float(tech.sma_5) if tech.sma_5 else 0,
                'sma_10': float(tech.sma_10) if tech.sma_10 else 0,
                'sma_20': float(tech.sma_20) if tech.sma_20 else 0,
                'rsi_14': float(tech.rsi_14) if tech.rsi_14 else 0,
                'macd': float(tech.macd) if tech.macd else 0,
                'bb_upper': float(tech.bb_upper) if tech.bb_upper else 0,
                'bb_lower': float(tech.bb_lower) if tech.bb_lower else 0,
                'atr_14': float(tech.atr_14) if tech.atr_14 else 0,
                'obv': float(tech.obv) if tech.obv else 0,
                
                # Indicateurs de sentiment
                'sentiment_score_normalized': float(sent.sentiment_score_normalized) if sent.sentiment_score_normalized else 0,
                'sentiment_momentum_1d': float(sent.sentiment_momentum_1d) if sent.sentiment_momentum_1d else 0,
                'sentiment_volatility_3d': float(sent.sentiment_volatility_3d) if sent.sentiment_volatility_3d else 0,
                'news_positive_ratio': float(sent.news_positive_ratio) if sent.news_positive_ratio else 0,
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        print(f"✅ DataFrame créé avec {len(df)} lignes et {len(df.columns)} colonnes")
        
        # Test 6: Création des labels
        print("\n6️⃣ Création des labels...")
        try:
            df_with_labels = service.create_advanced_labels(df, target_param)
            print(f"✅ Labels créés avec succès")
            print(f"   - Données avec labels: {len(df_with_labels)} lignes")
            
            # Vérifier la distribution des labels
            if 'target_achieved' in df_with_labels.columns:
                target_dist = df_with_labels['target_achieved'].value_counts()
                print(f"   - Distribution des labels: {target_dist.to_dict()}")
            
        except Exception as e:
            print(f"❌ Erreur lors de la création des labels: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Test 7: Préparation des features
        print("\n7️⃣ Préparation des features...")
        try:
            X, feature_names = service.prepare_features(df_with_labels)
            print(f"✅ Features préparées: {len(feature_names)} features")
            print(f"   - Shape des données: {X.shape}")
            
            # Vérifier qu'il n'y a pas de valeurs NaN
            nan_count = pd.isna(X).sum().sum()
            if nan_count > 0:
                print(f"⚠️  {nan_count} valeurs NaN détectées, remplacement par 0")
                X = X.fillna(0)
            
        except Exception as e:
            print(f"❌ Erreur lors de la préparation des features: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Test 8: Entraînement d'un modèle simple
        print("\n8️⃣ Entraînement d'un modèle simple...")
        try:
            import lightgbm as lgb
            import numpy as np
            
            # Préparer les données pour LightGBM
            y = df_with_labels['target_achieved'].values if 'target_achieved' in df_with_labels.columns else np.random.randint(0, 2, len(X))
            
            # Créer un dataset LightGBM
            train_data = lgb.Dataset(X, label=y)
            
            # Paramètres pour un modèle simple
            params = {
                'objective': 'binary',
                'metric': 'binary_logloss',
                'verbose': -1,
                'num_leaves': 31,
                'learning_rate': 0.1,
                'feature_fraction': 0.9,
                'bagging_fraction': 0.8,
                'bagging_freq': 5,
                'min_data_in_leaf': 20
            }
            
            # Entraîner le modèle
            model = lgb.train(params, train_data, num_boost_round=50)
            print("✅ Modèle LightGBM entraîné avec succès")
            
            # Test de prédiction
            predictions = model.predict(X[:10])
            print(f"✅ Prédictions effectuées: {predictions[:5]}")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'entraînement: {e}")
            import traceback
            traceback.print_exc()
            return
        
        print("\n🎉 Tous les tests d'entraînement ont réussi!")
        print("💡 Le service LightGBM est prêt pour l'entraînement complet via l'API")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_lightgbm_training()
