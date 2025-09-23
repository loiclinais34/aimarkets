"""
Endpoint de test simple pour LightGBM
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.database import TargetParameters

router = APIRouter()

@router.get("/test")
async def test_lightgbm_endpoint(db: Session = Depends(get_db)):
    """Test simple de l'endpoint LightGBM"""
    try:
        print("🧪 Test de l'endpoint LightGBM...")
        
        # Test 1: Vérification de la connexion à la base de données
        target_param = db.query(TargetParameters).first()
        if target_param:
            print(f"✅ Paramètre cible trouvé: {target_param.parameter_name}")
        else:
            print("❌ Aucun paramètre cible trouvé")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aucun paramètre cible trouvé"
            )
        
        # Test 2: Test d'import de LightGBM
        try:
            import lightgbm as lgb
            print(f"✅ LightGBM importé avec succès (version {lgb.__version__})")
        except Exception as e:
            print(f"❌ Erreur d'import LightGBM: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur d'import LightGBM: {str(e)}"
            )
        
        # Test 3: Test de création du service
        try:
            from app.services.lightgbm_service import LightGBMService
            service = LightGBMService(db)
            print("✅ Service LightGBM créé avec succès")
        except Exception as e:
            print(f"❌ Erreur lors de la création du service: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur lors de la création du service: {str(e)}"
            )
        
        return {
            "status": "success",
            "message": "Tous les tests LightGBM ont réussi",
            "lightgbm_version": lgb.__version__,
            "target_parameter": target_param.parameter_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur générale: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur générale: {str(e)}"
        )

@router.post("/train/simple")
async def train_simple_lightgbm_model(
    symbol: str = "AAPL",
    target_parameter_id: int = 5,
    db: Session = Depends(get_db)
):
    """Test d'entraînement simple LightGBM"""
    try:
        print(f"🚀 Test d'entraînement simple pour {symbol} avec paramètre {target_parameter_id}")
        
        # Récupération du paramètre cible
        target_param = db.query(TargetParameters).filter(
            TargetParameters.id == target_parameter_id
        ).first()
        
        if not target_param:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paramètre cible non trouvé"
            )
        
        print(f"✅ Paramètre cible trouvé: {target_param.parameter_name}")
        
        # Création du service
        from app.services.lightgbm_service import LightGBMService
        service = LightGBMService(db)
        print("✅ Service LightGBM créé")
        
        # Test d'entraînement minimal
        print("🔄 Début de l'entraînement...")
        result = service.train_binary_classification_model(
            symbol=symbol,
            target_param=target_param,
            db=db
        )
        print("✅ Entraînement terminé")
        
        return {
            "status": "success",
            "model_id": result["model_id"],
            "model_name": result["model_name"],
            "message": "Modèle LightGBM entraîné avec succès"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur lors de l'entraînement: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'entraînement: {str(e)}"
        )
