#!/usr/bin/env python3
"""
Script pour corriger les chemins de modèles manquants
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.database import MLModels
from sqlalchemy.orm import Session

def fix_model_paths():
    """Corriger les chemins de modèles manquants"""
    
    print("🔧 Correction des chemins de modèles manquants")
    print("=" * 60)
    
    db = next(get_db())
    try:
        # Récupérer tous les modèles
        all_models = db.query(MLModels).all()
        print(f"📊 {len(all_models)} modèles trouvés au total")
        
        # Identifier les modèles sans chemin
        models_without_path = db.query(MLModels).filter(
            MLModels.model_path.is_(None)
        ).all()
        
        print(f"❌ {len(models_without_path)} modèles sans chemin de fichier")
        
        # Identifier les modèles avec chemin invalide
        models_with_invalid_path = []
        for model in all_models:
            if model.model_path and not os.path.exists(model.model_path):
                models_with_invalid_path.append(model)
        
        print(f"❌ {len(models_with_invalid_path)} modèles avec chemin invalide")
        
        # Désactiver les modèles problématiques
        problematic_models = models_without_path + models_with_invalid_path
        
        if problematic_models:
            print(f"\n🔧 Désactivation de {len(problematic_models)} modèles problématiques...")
            
            for model in problematic_models:
                print(f"   ❌ {model.model_name} - {model.symbol}")
                print(f"      Chemin: {model.model_path}")
                model.is_active = False
            
            db.commit()
            print(f"✅ {len(problematic_models)} modèles désactivés")
        
        # Vérifier les modèles valides restants
        valid_models = db.query(MLModels).filter(
            MLModels.is_active == True,
            MLModels.model_path.isnot(None)
        ).all()
        
        print(f"\n✅ {len(valid_models)} modèles valides restants")
        
        # Vérifier que les fichiers existent
        valid_count = 0
        for model in valid_models:
            if os.path.exists(model.model_path):
                valid_count += 1
            else:
                print(f"   ⚠️ Fichier manquant: {model.model_path}")
                model.is_active = False
        
        db.commit()
        
        print(f"✅ {valid_count} modèles avec fichiers valides")
        
        # Statistiques par symbole
        print(f"\n📊 Statistiques par symbole:")
        symbols = db.query(MLModels.symbol).distinct().all()
        
        for symbol_tuple in symbols:
            symbol = symbol_tuple[0]
            active_models = db.query(MLModels).filter(
                MLModels.symbol == symbol,
                MLModels.is_active == True
            ).count()
            
            total_models = db.query(MLModels).filter(
                MLModels.symbol == symbol
            ).count()
            
            print(f"   {symbol}: {active_models}/{total_models} modèles actifs")
        
    finally:
        db.close()

def list_model_files():
    """Lister les fichiers de modèles disponibles"""
    
    print(f"\n📁 Fichiers de modèles disponibles")
    print("-" * 40)
    
    models_dir = "./models"
    if os.path.exists(models_dir):
        model_files = [f for f in os.listdir(models_dir) if f.endswith('.joblib')]
        print(f"📊 {len(model_files)} fichiers .joblib trouvés")
        
        for file in sorted(model_files)[:10]:  # Afficher les 10 premiers
            file_path = os.path.join(models_dir, file)
            file_size = os.path.getsize(file_path)
            print(f"   📄 {file} ({file_size} bytes)")
        
        if len(model_files) > 10:
            print(f"   ... et {len(model_files) - 10} autres fichiers")
    else:
        print(f"❌ Dossier {models_dir} non trouvé")

if __name__ == "__main__":
    print("🚀 Démarrage de la correction des chemins de modèles")
    
    list_model_files()
    fix_model_paths()
    
    print("\n🏁 Correction terminée")
