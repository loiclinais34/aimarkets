# Gestion des Quotas Alpha Vantage

## Limites de l'API gratuite

- **25 requêtes par jour** maximum
- **5 requêtes par minute** maximum
- **Pas de limite de temps** entre les requêtes (contrairement à Polygon.io)

## Configuration actuelle

### Paramètres par défaut
- `batch_size: 25` - Traite exactement 25 symboles par jour
- `delay_minutes: 0` - Pas de délai entre les requêtes
- Limitation automatique à 25 symboles maximum

### Stratégie de récupération

1. **Quotidienne** : 25 symboles par jour
2. **Incrémentale** : Mise à jour des symboles non traités depuis X jours
3. **Sélective** : Traitement de symboles spécifiques

## Utilisation recommandée

### Pour la production
```bash
# Lancer la récupération quotidienne (25 symboles)
curl -X POST "http://localhost:8000/api/v1/financial-ratios/update" \
  -H "Content-Type: application/json" \
  -d '{"batch_size": 25, "delay_minutes": 0}'
```

### Pour les tests
```bash
# Tester avec quelques symboles
curl -X POST "http://localhost:8000/api/v1/financial-ratios/update" \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "MSFT", "GOOGL"], "batch_size": 3, "delay_minutes": 0}'
```

## Surveillance des quotas

### Vérifier le statut d'une tâche
```bash
curl "http://localhost:8000/api/v1/financial-ratios/task-status/{task_id}"
```

### Statistiques des ratios
```bash
curl "http://localhost:8000/api/v1/financial-ratios/stats"
```

## Planification automatique

### Cron job quotidien (recommandé)
```bash
# Ajouter à crontab pour exécution quotidienne à 9h00
0 9 * * * cd /path/to/aimarkets/backend && python3 -c "
from app.tasks.financial_ratios_tasks import update_financial_ratios_task
update_financial_ratios_task.delay()
"
```

### Alternative avec Celery Beat
```python
# Dans celery_app.py
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'daily-financial-ratios': {
        'task': 'app.tasks.financial_ratios_tasks.update_financial_ratios_task',
        'schedule': crontab(hour=9, minute=0),  # 9h00 tous les jours
    },
}
```

## Gestion des erreurs

### Quota dépassé
- L'API retourne une erreur 429
- Le système log l'erreur et arrête le traitement
- Reprendre le lendemain

### Symboles sans données
- Certains symboles peuvent ne pas avoir de données Alpha Vantage
- Le système continue avec les symboles suivants
- Les erreurs sont loggées mais n'interrompent pas le processus

## Optimisations futures

### Passage au plan premium
- **75 requêtes par minute** (au lieu de 5)
- **Pas de limite quotidienne**
- **Coût** : 49.99$/mois

### Mise en cache
- Stocker les données récupérées
- Éviter les requêtes répétées
- Mise à jour incrémentale

### Parallélisation
- Traitement de plusieurs symboles en parallèle
- Respect des limites de taux (5 req/min)
- Optimisation du temps de traitement
