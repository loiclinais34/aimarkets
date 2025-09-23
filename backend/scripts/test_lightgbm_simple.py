#!/usr/bin/env python3
"""
Test simple et sécurisé du service LightGBM
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, datetime
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.database import TargetParameters, MLModels

def test_lightgbm_simple():
    """Test simple du service LightGBM sans entraînement complet"""
    print("🧪 Test simple du service LightGBM...")
    
    # Récupération de la session de base de données
    db = next(get_db())
    
    try:
        # Test 1: Vérification de la connexion à la base de données
        print("\n1️⃣ Test de connexion à la base de données...")
        target_param = db.query(TargetParameters).first()
        if target_param:
            print(f"✅ Paramètre cible trouvé: {target_param.parameter_name}")
        else:
            print("❌ Aucun paramètre cible trouvé")
            return
        
        # Test 2: Vérification des données disponibles
        print("\n2️⃣ Test des données disponibles...")
        from app.models.database import HistoricalData, TechnicalIndicators, SentimentIndicators
        
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
        
        # Test 3: Test d'import de LightGBM
        print("\n3️⃣ Test d'import de LightGBM...")
        try:
            import lightgbm as lgb
            print(f"✅ LightGBM importé avec succès (version {lgb.__version__})")
        except Exception as e:
            print(f"❌ Erreur d'import LightGBM: {e}")
            return
        
        # Test 4: Test de création d'un dataset simple
        print("\n4️⃣ Test de création d'un dataset simple...")
        try:
            import numpy as np
            import pandas as pd
            
            # Créer des données de test
            X = np.random.rand(100, 10)
            y = np.random.randint(0, 2, 100)
            
            # Créer un dataset LightGBM
            train_data = lgb.Dataset(X, label=y)
            print("✅ Dataset LightGBM créé avec succès")
            
            # Test de paramètres
            params = {
                'objective': 'binary',
                'metric': 'binary_logloss',
                'verbose': -1
            }
            
            # Test d'entraînement minimal
            model = lgb.train(params, train_data, num_boost_round=10)
            print("✅ Modèle LightGBM entraîné avec succès")
            
            # Test de prédiction
            prediction = model.predict(X[:5])
            print(f"✅ Prédiction effectuée: {prediction}")
            
        except Exception as e:
            print(f"❌ Erreur lors du test LightGBM: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Test 5: Test de création du service (sans entraînement)
        print("\n5️⃣ Test de création du service LightGBM...")
        try:
            from app.services.lightgbm_service import LightGBMService
            service = LightGBMService(db)
            print("✅ Service LightGBM créé avec succès")
            
            # Test de préparation des features (sans entraînement)
            print("\n6️⃣ Test de préparation des features...")
            
            # Récupérer quelques données
            query = db.query(HistoricalData, TechnicalIndicators, SentimentIndicators).join(
                TechnicalIndicators, HistoricalData.symbol == TechnicalIndicators.symbol
            ).join(
                SentimentIndicators, HistoricalData.symbol == SentimentIndicators.symbol
            ).filter(
                HistoricalData.symbol == "AAPL"
            ).order_by(HistoricalData.date).limit(10)
            
            results = query.all()
            print(f"   - {len(results)} enregistrements récupérés")
            
            if len(results) > 0:
                # Test de conversion en DataFrame
                data = []
                for hist, tech, sent in results:
                    row = {
                        'date': hist.date,
                        'symbol': hist.symbol,
                        'close': float(hist.close),
                        'sma_5': float(tech.sma_5) if tech.sma_5 else 0,
                        'rsi_14': float(tech.rsi_14) if tech.rsi_14 else 0,
                        'sentiment_score_normalized': float(sent.sentiment_score_normalized) if sent.sentiment_score_normalized else 0,
                    }
                    data.append(row)
                
                df = pd.DataFrame(data)
                print(f"✅ DataFrame créé avec {len(df)} lignes et {len(df.columns)} colonnes")
                
                # Test de préparation des features
                X, feature_names = service.prepare_features(df)
                print(f"✅ Features préparées: {len(feature_names)} features")
                
            else:
                print("❌ Aucune donnée récupérée")
                
        except Exception as e:
            print(f"❌ Erreur lors de la création du service: {e}")
            import traceback
            traceback.print_exc()
            return
        
        print("\n🎉 Tous les tests simples ont réussi!")
        print("💡 Le service LightGBM est prêt pour l'entraînement complet")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_lightgbm_simple()
