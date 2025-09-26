#!/usr/bin/env python3
"""
Script de test pour la nouvelle logique de recherche d'opportunités
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.ml_service import MLService
from app.services.screener_service import ScreenerService
from app.models.database import TargetParameters, SymbolMetadata, MLModels
from decimal import Decimal
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_opportunity_search_logic():
    """Test de la nouvelle logique de recherche d'opportunités"""
    
    print("🔍 Test de la nouvelle logique de recherche d'opportunités")
    print("=" * 80)
    
    # Paramètres de test
    target_return_percentage = 5.0  # 5% de rendement attendu
    time_horizon_days = 10  # 10 jours d'horizon
    risk_tolerance = 0.5  # Tolérance au risque modérée
    
    print(f"📊 Paramètres de test:")
    print(f"  - Rendement attendu: {target_return_percentage}%")
    print(f"  - Horizon temporel: {time_horizon_days} jours")
    print(f"  - Tolérance au risque: {risk_tolerance}")
    
    # Récupérer quelques symboles pour le test
    db = next(get_db())
    try:
        # Récupérer les 3 premiers symboles
        symbol_records = db.query(SymbolMetadata).limit(3).all()
        test_symbols = [record.symbol for record in symbol_records]
        
        print(f"\n🎯 Symboles de test: {test_symbols}")
        
        # Initialiser les services
        ml_service = MLService(db=db)
        screener_service = ScreenerService(db=db)
        
        # Tester chaque symbole
        for symbol in test_symbols:
            print(f"\n{'='*50}")
            print(f"🔍 Test pour {symbol}")
            print(f"{'='*50}")
            
            # Créer les paramètres de cible
            target_param = screener_service._get_or_create_target_parameter(
                symbol=symbol,
                target_return_percentage=target_return_percentage,
                time_horizon_days=time_horizon_days,
                risk_tolerance=risk_tolerance,
                user_id="test_user"
            )
            
            print(f"✅ Paramètres créés: ID={target_param.id}")
            print(f"   - Rendement: {target_param.target_return_percentage}%")
            print(f"   - Horizon: {target_param.time_horizon_days} jours")
            
            # Créer les données d'entraînement avec la nouvelle logique
            df = ml_service.create_labels_for_training(symbol, target_param, db)
            
            if df.empty:
                print(f"❌ Aucune donnée d'entraînement pour {symbol}")
                continue
            
            print(f"📊 Données d'entraînement créées:")
            print(f"   - Échantillons: {len(df)}")
            print(f"   - Échantillons positifs: {df['target_achieved'].sum()}")
            print(f"   - Taux de positifs: {df['target_achieved'].mean()*100:.1f}%")
            
            # Afficher quelques exemples
            print(f"\n📋 Exemples de données:")
            sample_df = df[['date', 'close', 'target_price', 'future_close', 'target_achieved']].head(3)
            for _, row in sample_df.iterrows():
                print(f"   {row['date']}: Prix={row['close']:.2f} → Cible={row['target_price']:.2f} → Futur={row['future_close']:.2f} → Atteint={row['target_achieved']}")
            
            # Entraîner les modèles
            print(f"\n🤖 Entraînement des modèles...")
            results = ml_service.train_multiple_models(
                symbol=symbol,
                target_param=target_param,
                algorithms=['RandomForest', 'XGBoost', 'LightGBM', 'NeuralNetwork'],
                db=db
            )
            
            print(f"📊 Résultats d'entraînement:")
            for algorithm, result in results.items():
                if "error" not in result:
                    accuracy = result.get('accuracy', 0)
                    f1_score = result.get('f1_score', 0)
                    print(f"   ✅ {algorithm}: Accuracy={accuracy:.3f}, F1={f1_score:.3f}")
                else:
                    print(f"   ❌ {algorithm}: {result['error']}")
            
            # Vérifier que les modèles utilisent bien les paramètres utilisateur
            print(f"\n🔍 Vérification des paramètres dans les modèles:")
            models = db.query(MLModels).filter(
                MLModels.symbol == symbol,
                MLModels.target_parameter_id == target_param.id
            ).all()
            
            for model in models:
                params = model.model_parameters
                print(f"   📋 {model.model_name}:")
                print(f"      - Algorithme: {params.get('algorithm', 'N/A')}")
                print(f"      - Rendement cible: {params.get('target_return_percentage', 'N/A')}%")
                print(f"      - Horizon: {params.get('time_horizon_days', 'N/A')} jours")
                print(f"      - Performance: {model.performance_metrics.get('accuracy', 0):.3f}")
        
        print(f"\n{'='*80}")
        print("✅ Test terminé avec succès!")
        
    finally:
        db.close()

def test_target_calculation():
    """Test du calcul de prix cible"""
    
    print("\n🧮 Test du calcul de prix cible")
    print("=" * 50)
    
    # Exemple: titre à 100$ avec 5% de rendement sur 10 jours
    current_price = 100.0
    target_return = 5.0
    time_horizon = 10
    
    # Calcul du prix cible
    target_price = current_price * (1 + target_return / 100)
    
    print(f"📊 Exemple de calcul:")
    print(f"   - Prix actuel: ${current_price:.2f}")
    print(f"   - Rendement attendu: {target_return}%")
    print(f"   - Horizon: {time_horizon} jours")
    print(f"   - Prix cible: ${target_price:.2f}")
    
    # Simulation de données d'entraînement
    print(f"\n📋 Simulation de données d'entraînement:")
    print(f"   - Données du 2025-09-01 au 2025-09-10")
    print(f"   - Cours cible du 2025-09-20: ${target_price:.2f}")
    print(f"   - Le modèle apprend à prédire si le prix atteint ${target_price:.2f} en {time_horizon} jours")

if __name__ == "__main__":
    print("🚀 Démarrage des tests de la logique de recherche d'opportunités")
    
    # Test du calcul de prix cible
    test_target_calculation()
    
    # Test de la logique complète
    test_opportunity_search_logic()
    
    print("\n🏁 Tests terminés")
