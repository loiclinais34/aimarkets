"""
Script de recalcul des indicateurs de bulle pour tous les symboles
"""

import sys
sys.path.append('/Users/loiclinais/Documents/dev/aimarkets/backend')

import argparse
import logging
from datetime import date
from app.core.database import SessionLocal
from app.services.bubble_detection import BubbleDetectionService
from app.services.data_update_service import DataUpdateService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def recompute_bubble_indicators_for_all_symbols(
    analysis_date: date = None,
    force_update: bool = False
):
    """
    Recalcule les indicateurs de bulle pour tous les symboles actifs
    
    Args:
        analysis_date: Date d'analyse (par défaut aujourd'hui)
        force_update: Forcer le recalcul même si déjà fait
    """
    if analysis_date is None:
        analysis_date = date.today()
    
    db = SessionLocal()
    
    try:
        logger.info(f"Début du recalcul des indicateurs de bulle pour le {analysis_date}")
        
        # Récupérer tous les symboles actifs
        data_service = DataUpdateService(db)
        symbols = data_service.get_active_symbols()
        total_symbols = len(symbols)
        
        logger.info(f"Total de {total_symbols} symboles à analyser")
        
        # Initialiser le service de détection de bulles
        bubble_service = BubbleDetectionService(db)
        
        # Statistiques
        successful = 0
        failed = 0
        skipped = 0
        results = []
        
        # Traiter chaque symbole
        for i, symbol in enumerate(symbols, 1):
            try:
                logger.info(f"[{i}/{total_symbols}] Analyse de {symbol}")
                
                # Vérifier si déjà calculé aujourd'hui (sauf si force_update)
                if not force_update:
                    from app.models.bubble_indicators import BubbleIndicators
                    existing = db.query(BubbleIndicators).filter(
                        BubbleIndicators.symbol == symbol,
                        BubbleIndicators.analysis_date == analysis_date
                    ).first()
                    
                    if existing:
                        logger.info(f"  ⏭️  {symbol}: déjà calculé pour {analysis_date} (utilisez --force pour recalculer)")
                        skipped += 1
                        continue
                
                # Analyser le risque de bulle
                bubble_data = bubble_service.analyze_bubble_risk(
                    symbol=symbol,
                    analysis_date=analysis_date,
                    db=db
                )
                
                if 'error' not in bubble_data:
                    # Sauvegarder les indicateurs
                    saved = bubble_service.save_bubble_indicators(bubble_data, db)
                    
                    if saved:
                        logger.info(f"  ✅ {symbol}: Score={bubble_data['bubble_score']:.2f} ({bubble_data['bubble_level']})")
                        successful += 1
                        results.append({
                            'symbol': symbol,
                            'score': bubble_data['bubble_score'],
                            'level': bubble_data['bubble_level'],
                            'status': 'success'
                        })
                    else:
                        logger.warning(f"  ⚠️  {symbol}: Analyse réussie mais sauvegarde échouée")
                        failed += 1
                else:
                    logger.error(f"  ❌ {symbol}: Erreur - {bubble_data.get('error')}")
                    failed += 1
                    results.append({
                        'symbol': symbol,
                        'status': 'error',
                        'error': bubble_data.get('error')
                    })
                
            except Exception as e:
                logger.error(f"  ❌ {symbol}: Exception - {e}")
                failed += 1
                results.append({
                    'symbol': symbol,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Afficher le résumé
        logger.info("=" * 80)
        logger.info("RÉSUMÉ DU RECALCUL")
        logger.info("=" * 80)
        logger.info(f"Total de symboles: {total_symbols}")
        logger.info(f"✅ Réussis: {successful}")
        logger.info(f"⏭️  Ignorés: {skipped}")
        logger.info(f"❌ Échoués: {failed}")
        logger.info("")
        
        # Afficher les alertes de bulle
        high_risk_bubbles = [r for r in results if r.get('status') == 'success' and r.get('level') in ['RISK', 'PROBABLE', 'CRITICAL']]
        watch_bubbles = [r for r in results if r.get('status') == 'success' and r.get('level') == 'WATCH']
        
        if high_risk_bubbles:
            logger.info("🚨 ALERTES DE BULLE À HAUT RISQUE:")
            for r in sorted(high_risk_bubbles, key=lambda x: x['score'], reverse=True):
                logger.info(f"  ⚠️  {r['symbol']}: {r['level']} (score: {r['score']:.2f})")
            logger.info("")
        
        if watch_bubbles:
            logger.info("⚡ TITRES À SURVEILLER:")
            for r in sorted(watch_bubbles, key=lambda x: x['score'], reverse=True):
                logger.info(f"  👀 {r['symbol']}: WATCH (score: {r['score']:.2f})")
            logger.info("")
        
        # Top 10 scores
        top_scores = sorted([r for r in results if r.get('status') == 'success'], 
                           key=lambda x: x['score'], reverse=True)[:10]
        
        if top_scores:
            logger.info("📊 TOP 10 SCORES DE BULLE:")
            for r in top_scores:
                logger.info(f"  {r['symbol']}: {r['score']:.2f}/100 ({r['level']})")
        
        logger.info("")
        logger.info("✅ Recalcul terminé!")
        
        return {
            'total': total_symbols,
            'successful': successful,
            'skipped': skipped,
            'failed': failed,
            'high_risk': len(high_risk_bubbles),
            'watch': len(watch_bubbles),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du recalcul des indicateurs de bulle: {e}")
        raise
    finally:
        db.close()


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description='Recalcul des indicateurs de bulle')
    parser.add_argument('--symbols', type=str, help='Symboles à analyser (séparés par des virgules)', default=None)
    parser.add_argument('--force', action='store_true', help='Forcer le recalcul même si déjà fait')
    parser.add_argument('--date', type=str, help='Date d\'analyse (YYYY-MM-DD)', default=None)
    
    args = parser.parse_args()
    
    # Déterminer la date d'analyse
    if args.date:
        from datetime import datetime
        analysis_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    else:
        analysis_date = date.today()
    
    logger.info(f"Date d'analyse: {analysis_date}")
    logger.info(f"Force update: {args.force}")
    
    # Si des symboles spécifiques sont fournis
    if args.symbols:
        symbols_list = [s.strip().upper() for s in args.symbols.split(',')]
        logger.info(f"Symboles spécifiés: {symbols_list}")
        
        db = SessionLocal()
        bubble_service = BubbleDetectionService(db)
        
        for symbol in symbols_list:
            try:
                bubble_data = bubble_service.analyze_bubble_risk(symbol, analysis_date, db)
                if 'error' not in bubble_data:
                    bubble_service.save_bubble_indicators(bubble_data, db)
                    logger.info(f"✅ {symbol}: Score={bubble_data['bubble_score']:.2f} ({bubble_data['bubble_level']})")
                else:
                    logger.error(f"❌ {symbol}: {bubble_data['error']}")
            except Exception as e:
                logger.error(f"❌ {symbol}: {e}")
        
        db.close()
    else:
        # Recalculer pour tous les symboles
        recompute_bubble_indicators_for_all_symbols(analysis_date, args.force)


if __name__ == "__main__":
    main()
