#!/usr/bin/env python3
"""
Script de diagnostic pour tester le service ML directement
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.services.ml_service import MLService
from app.models.database import TargetParameters, HistoricalData, TechnicalIndicators, SentimentIndicators
from datetime import date

def test_ml_service():
    """Tester le service ML directement"""
    print("🔧 Test du service ML...")
    
    db = SessionLocal()
    try:
        # Test 1: Vérifier la connexion DB
        print("✅ Connexion DB réussie")
        
        # Test 2: Vérifier les données disponibles
        symbols_count = db.query(HistoricalData.symbol).distinct().count()
        print(f"📊 Nombre de symboles avec données historiques: {symbols_count}")
        
        # Test 3: Vérifier les indicateurs techniques
        tech_count = db.query(TechnicalIndicators).count()
        print(f"📊 Nombre d'indicateurs techniques: {tech_count}")
        
        # Test 4: Vérifier les indicateurs de sentiment
        sent_count = db.query(SentimentIndicators).count()
        print(f"📊 Nombre d'indicateurs de sentiment: {sent_count}")
        
        # Test 5: Tester l'instanciation du service ML
        print("🔧 Test instanciation MLService...")
        ml_service = MLService(db)
        print(f"✅ MLService instancié: {type(ml_service)}")
        print(f"✅ Chemin des modèles: {ml_service.models_path}")
        
        # Test 6: Vérifier les données pour AAPL
        print("🔧 Test données AAPL...")
        aapl_data = db.query(HistoricalData).filter(HistoricalData.symbol == "AAPL").count()
        print(f"📊 Données historiques AAPL: {aapl_data}")
        
        aapl_tech = db.query(TechnicalIndicators).filter(TechnicalIndicators.symbol == "AAPL").count()
        print(f"📊 Indicateurs techniques AAPL: {aapl_tech}")
        
        aapl_sent = db.query(SentimentIndicators).filter(SentimentIndicators.symbol == "AAPL").count()
        print(f"📊 Indicateurs de sentiment AAPL: {aapl_sent}")
        
        # Test 7: Créer un paramètre de cible
        print("🔧 Test création paramètre de cible...")
        target_param = TargetParameters(
            user_id="test_user",
            parameter_name="test_target_AAPL_3%_26d",
            target_return_percentage=3.0,
            time_horizon_days=26,
            risk_tolerance="medium",
            min_confidence_threshold=0.7,
            max_drawdown_percentage=5.0
        )
        db.add(target_param)
        db.commit()
        db.refresh(target_param)
        print(f"✅ Paramètre de cible créé: {target_param.id}")
        
        # Test 8: Tester la création des données d'entraînement
        print("🔧 Test création données d'entraînement...")
        try:
            df = ml_service.create_labels_for_training("AAPL", target_param, db)
            print(f"✅ DataFrame créé: {len(df)} lignes, {len(df.columns)} colonnes")
            if not df.empty:
                print(f"📊 Colonnes: {list(df.columns)[:5]}...")
                print(f"📊 Première ligne: {df.iloc[0].to_dict() if len(df) > 0 else 'Vide'}")
            else:
                print("⚠️  DataFrame vide - pas assez de données")
        except Exception as e:
            print(f"❌ Erreur création DataFrame: {e}")
            import traceback
            traceback.print_exc()
        
        # Nettoyage
        db.delete(target_param)
        db.commit()
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print("✅ Session DB fermée")

if __name__ == "__main__":
    test_ml_service()
