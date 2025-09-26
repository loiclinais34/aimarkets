"""
Tâches Celery pour la récupération des ratios financiers
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from celery import current_task
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.financial_ratios_service import FinancialRatiosService
from app.models.database import SymbolMetadata, FinancialRatios
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def update_financial_ratios_task(self, symbols: List[str] = None, batch_size: int = 25, delay_minutes: int = 0):
    """
    Tâche pour récupérer les ratios financiers pour tous les symboles
    
    Args:
        symbols: Liste des symboles à traiter (optionnel, si None récupère tous les symboles)
        batch_size: Taille des lots (défaut: 25 - limite Alpha Vantage gratuite)
        delay_minutes: Délai en minutes entre les lots (défaut: 0 - pas de délai pour 25 symboles/jour)
    
    Returns:
        Dictionnaire avec les résultats
    """
    try:
        logger.info(f"Démarrage de la récupération des ratios financiers")
        
        # Récupérer les symboles si non fournis
        if symbols is None:
            db = next(get_db())
            try:
                symbol_records = db.query(SymbolMetadata).all()
                symbols = [record.symbol for record in symbol_records]
                logger.info(f"Récupération de {len(symbols)} symboles depuis la base de données")
            finally:
                db.close()
        
        # Exclure AAPL si déjà traité
        symbols = [s for s in symbols if s != 'AAPL']
        
        # Limiter à 25 symboles maximum (quota Alpha Vantage gratuit)
        if len(symbols) > 25:
            symbols = symbols[:25]
            logger.warning(f"Limitation à 25 symboles (quota Alpha Vantage gratuit): {symbols}")
        
        if not symbols:
            logger.info("Aucun symbole à traiter")
            return {
                'status': 'completed',
                'message': 'Aucun symbole à traiter',
                'total_symbols': 0,
                'successful_updates': 0,
                'failed_updates': 0,
                'results': []
            }
        
        total_symbols = len(symbols)
        logger.info(f"Traitement de {total_symbols} symboles (limite Alpha Vantage: 25/jour)")
        
        # Diviser en lots
        batches = [symbols[i:i + batch_size] for i in range(0, len(symbols), batch_size)]
        total_batches = len(batches)
        
        results = []
        successful_updates = 0
        failed_updates = 0
        
        # Traiter chaque lot
        for batch_index, batch_symbols in enumerate(batches):
            try:
                # Mettre à jour le statut
                progress = int((batch_index / total_batches) * 100)
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'status': f'Traitement du lot {batch_index + 1}/{total_batches}',
                        'progress': progress,
                        'current_batch': batch_index + 1,
                        'total_batches': total_batches,
                        'current_symbols': batch_symbols,
                        'successful_updates': successful_updates,
                        'failed_updates': failed_updates
                    }
                )
                
                logger.info(f"Traitement du lot {batch_index + 1}/{total_batches}: {batch_symbols}")
                
                # Traiter chaque symbole du lot
                for symbol_index, symbol in enumerate(batch_symbols):
                    try:
                        # Mettre à jour le statut pour le symbole
                        symbol_progress = int(((batch_index * batch_size + symbol_index) / total_symbols) * 100)
                        self.update_state(
                            state='PROGRESS',
                            meta={
                                'status': f'Traitement de {symbol} (lot {batch_index + 1}/{total_batches})',
                                'progress': symbol_progress,
                                'current_batch': batch_index + 1,
                                'total_batches': total_batches,
                                'current_symbol': symbol,
                                'current_symbols': batch_symbols,
                                'successful_updates': successful_updates,
                                'failed_updates': failed_updates
                            }
                        )
                        
                        # Récupérer et sauvegarder les ratios financiers
                        service = FinancialRatiosService()
                        db = next(get_db())
                        
                        try:
                            success = service.save_financial_ratios(db, symbol)
                            
                            if success:
                                result = {
                                    'symbol': symbol,
                                    'status': 'success',
                                    'message': 'Ratios financiers récupérés et sauvegardés avec succès'
                                }
                                successful_updates += 1
                                logger.info(f"✅ {symbol}: Ratios financiers sauvegardés")
                            else:
                                result = {
                                    'symbol': symbol,
                                    'status': 'error',
                                    'message': 'Erreur lors de la récupération des ratios financiers'
                                }
                                failed_updates += 1
                                logger.error(f"❌ {symbol}: Erreur lors de la sauvegarde")
                            
                            results.append(result)
                            
                        finally:
                            db.close()
                            
                    except Exception as e:
                        logger.error(f"Erreur lors du traitement de {symbol}: {e}")
                        results.append({
                            'symbol': symbol,
                            'status': 'error',
                            'message': str(e)
                        })
                        failed_updates += 1
                
                # Délai entre les lots (sauf pour le dernier lot)
                if batch_index < total_batches - 1:
                    delay_seconds = delay_minutes * 60
                    logger.info(f"Attente de {delay_minutes} minutes avant le prochain lot...")
                    
                    # Mettre à jour le statut pendant l'attente
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'status': f'Attente de {delay_minutes} minutes avant le prochain lot',
                            'progress': int(((batch_index + 1) / total_batches) * 100),
                            'current_batch': batch_index + 1,
                            'total_batches': total_batches,
                            'waiting_seconds': delay_seconds,
                            'successful_updates': successful_updates,
                            'failed_updates': failed_updates
                        }
                    )
                    
                    # Attendre
                    import time
                    time.sleep(delay_seconds)
                
            except Exception as e:
                logger.error(f"Erreur lors du traitement du lot {batch_index + 1}: {e}")
                # Marquer tous les symboles du lot comme échoués
                for symbol in batch_symbols:
                    results.append({
                        'symbol': symbol,
                        'status': 'error',
                        'message': f'Erreur du lot: {str(e)}'
                    })
                    failed_updates += 1
        
        # Résultat final
        final_result = {
            'status': 'completed',
            'total_symbols': total_symbols,
            'total_batches': total_batches,
            'successful_updates': successful_updates,
            'failed_updates': failed_updates,
            'results': results,
            'completion_time': datetime.now().isoformat()
        }
        
        self.update_state(state='SUCCESS', meta=final_result)
        logger.info(f"Récupération des ratios financiers terminée: {successful_updates}/{total_symbols} réussis")
        
        return final_result
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des ratios financiers: {e}", exc_info=True)
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

@celery_app.task(bind=True)
def update_financial_ratios_for_symbols_task(self, symbols: List[str]):
    """
    Tâche pour récupérer les ratios financiers pour une liste spécifique de symboles
    
    Args:
        symbols: Liste des symboles à traiter
    
    Returns:
        Dictionnaire avec les résultats
    """
    return update_financial_ratios_task.delay(symbols=symbols)

@celery_app.task(bind=True)
def update_financial_ratios_incremental_task(self, days_since_update: int = 30):
    """
    Tâche pour mettre à jour les ratios financiers des symboles non mis à jour depuis X jours
    
    Args:
        days_since_update: Nombre de jours depuis la dernière mise à jour
    
    Returns:
        Dictionnaire avec les résultats
    """
    try:
        logger.info(f"Récupération des symboles non mis à jour depuis {days_since_update} jours")
        
        # Date limite
        cutoff_date = datetime.now() - timedelta(days=days_since_update)
        
        # Récupérer les symboles à mettre à jour
        db = next(get_db())
        try:
            # Symboles sans ratios financiers
            symbols_without_ratios = db.query(SymbolMetadata.symbol).filter(
                ~SymbolMetadata.symbol.in_(
                    db.query(FinancialRatios.symbol)
                )
            ).all()
            
            # Symboles avec ratios financiers obsolètes
            symbols_with_old_ratios = db.query(FinancialRatios.symbol).filter(
                FinancialRatios.last_updated < cutoff_date
            ).all()
            
            # Combiner les listes
            symbols_to_update = list(set(
                [s[0] for s in symbols_without_ratios] + 
                [s[0] for s in symbols_with_old_ratios]
            ))
            
            logger.info(f"Symboles à mettre à jour: {len(symbols_to_update)}")
            
        finally:
            db.close()
        
        if not symbols_to_update:
            return {
                'status': 'completed',
                'message': 'Aucun symbole à mettre à jour',
                'total_symbols': 0,
                'successful_updates': 0,
                'failed_updates': 0,
                'results': []
            }
        
        # Lancer la tâche de mise à jour
        return update_financial_ratios_task.delay(symbols=symbols_to_update)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des symboles à mettre à jour: {e}", exc_info=True)
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise
