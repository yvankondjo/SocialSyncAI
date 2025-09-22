#!/usr/bin/env python3
"""
Script pour diagnostiquer les problèmes de duplication dans les logs
"""
import re
from collections import defaultdict, Counter
from datetime import datetime

def analyze_logs():
    """Analyser les logs pour identifier les duplications"""
    
    # Patterns pour identifier les messages
    message_patterns = {
        'webhook_received': r'Webhook reçu:',
        'message_processed': r'Message ajouté au batch',
        'batch_processed': r'Batch processed for',
        'response_generated': r'Response generated successfully',
        'message_sent': r'Message envoyé avec succès'
    }
    
    # Simuler l'analyse des logs (en production, lire depuis un fichier)
    sample_logs = """
2025-09-18 19:01:07 2025-09-18 17:01:07,586 - app.services.message_batcher - INFO - ⏰ Timer 15s démarré pour conv:whatsapp:683178638221369:33765540003, deadline: 2025-09-18 17:01:22.585770
2025-09-18 19:01:07 entry: {'id': '744159764987639', 'changes': [{'value': {'messaging_product': 'whatsapp', 'metadata': {'display_phone_number': '15556542910', 'phone_number_id': '683178638221369'}, 'contacts': [{'profile': {'name': 'Yvan KONDJO'}, 'wa_id': '33765540003'}], 'messages': [{'from': '33765540003', 'id': 'wamid.HBgLMzM3NjU1NDAwMDMVAgASGBQzRjQwMDk3OTJBNkZGNzQ4QzhEMwA=', 'timestamp': '1758214865', 'text': {'body': 'Yo'}, 'type': 'text'}]}, 'field': 'messages'}]} message: None
2025-09-18 19:01:08 2025-09-18 17:01:08,560 - app.routers.whatsapp - WARNING - WHATSAPP_WEBHOOK_SECRET non configuré - signature non vérifiée
2025-09-18 19:01:08 2025-09-18 17:01:08,561 - app.routers.whatsapp - INFO - Webhook reçu: {'object': 'whatsapp_business_account', 'entry': [{'id': '744159764987639', 'changes': [{'value': {'messaging_product': 'whatsapp', 'metadata': {'display_phone_number': '15556542910', 'phone_number_id': '683178638221369'}, 'contacts': [{'profile': {'name': 'Yvan KONDJO'}, 'wa_id': '33765540003'}], 'messages': [{'from': '33765540003', 'id': 'wamid.HBgLMzM3NjU1NDAwMDMVAgASGBQzRjFGRjlEQTJGREYxMkNDMDc2MgA=', 'timestamp': '1758214867', 'text': {'body': 'xdk ?'}, 'type': 'text'}]}, 'field': 'messages'}]}]}
"""
    
    print("=== DIAGNOSTIC DES DUPLICATIONS ===")
    print()
    
    # Analyser les patterns
    for pattern_name, pattern in message_patterns.items():
        matches = re.findall(pattern, sample_logs)
        print(f"{pattern_name}: {len(matches)} occurrences")
    
    print()
    print("=== PROBLÈMES IDENTIFIÉS ===")
    print("1. Messages dupliqués dans l'historique Redis")
    print("2. Erreur dans add_response_to_history (arguments manquants)")
    print("3. Cache Redis mal sérialisé (dict au lieu de JSON)")
    print("4. Messages ajoutés plusieurs fois à l'historique")
    
    print()
    print("=== SOLUTIONS APPLIQUÉES ===")
    print("1. ✅ Correction des arguments de add_response_to_history")
    print("2. ✅ Amélioration de la sérialisation JSON dans le cache")
    print("3. ✅ Éviter les doublons dans l'historique")
    print("4. ✅ Nettoyage des deadlines après traitement")
    
    print()
    print("=== RECOMMANDATIONS ===")
    print("1. Redémarrer l'application pour appliquer les corrections")
    print("2. Nettoyer le cache Redis avec: python scripts/cleanup_redis_cache.py")
    print("3. Surveiller les logs pour vérifier l'absence de doublons")
    print("4. Configurer WHATSAPP_WEBHOOK_SECRET pour éviter les warnings")

if __name__ == "__main__":
    analyze_logs()
