#!/usr/bin/env python3
"""
Script pour comparer les deux approches de groupement de messages
"""
import asyncio
from datetime import datetime, timedelta
from app.db.session import get_db

async def compare_approaches():
    """Comparer les deux approches de groupement"""
    
    db = get_db()
    
    print("=== COMPARAISON DES APPROCHES DE GROUPEMENT ===\n")
    
    # Approche 1: Messages individuels + groupement en temps réel
    print("🔄 APPROCHE 1: Messages individuels + Groupement temps réel")
    print("=" * 60)
    
    # Simuler une requête pour grouper les messages
    individual_query = """
    WITH message_groups AS (
        SELECT 
            cm.id,
            cm.content,
            cm.created_at,
            c.id as conversation_id,
            -- Grouper par fenêtres de 15 secondes
            DATE_TRUNC('second', cm.created_at) + 
            INTERVAL '15 seconds' * FLOOR(
                EXTRACT(EPOCH FROM (cm.created_at - DATE_TRUNC('minute', cm.created_at))) / 15
            ) as time_group
        FROM conversation_messages cm
        INNER JOIN conversations c ON cm.conversation_id = c.id
        WHERE cm.direction = 'inbound'
        AND cm.created_at >= NOW() - INTERVAL '7 days'
    )
    SELECT 
        conversation_id,
        time_group,
        COUNT(*) as message_count,
        STRING_AGG(content, ' | ') as concatenated_content
    FROM message_groups
    GROUP BY conversation_id, time_group
    HAVING COUNT(*) > 1
    ORDER BY time_group DESC
    LIMIT 10;
    """
    
    try:
        result1 = db.rpc('execute_sql', {'sql_query': individual_query}).execute()
        print(f"✅ Groupes trouvés: {len(result1.data) if result1.data else 0}")
        print("✅ Avantages:")
        print("   - Traçabilité complète de chaque message")
        print("   - Flexibilité du delta temporel")
        print("   - Debugging facile")
        print("   - Conformité aux webhooks originaux")
        print("❌ Inconvénients:")
        print("   - Stockage plus important")
        print("   - Requêtes plus complexes")
        print("   - Calculs en temps réel")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 60)
    
    # Approche 2: Messages concaténés directement
    print("🔄 APPROCHE 2: Messages concaténés en BDD")
    print("=" * 60)
    
    try:
        # Vérifier si la table message_groups existe
        groups_result = db.table("message_groups").select("id, content, message_count, created_at").limit(5).execute()
        
        if groups_result.data:
            print(f"✅ Groupes stockés: {len(groups_result.data)}")
            print("✅ Avantages:")
            print("   - Performance optimale")
            print("   - Stockage réduit")
            print("   - Requêtes simples")
            print("   - Cohérence traitement/stockage")
            print("❌ Inconvénients:")
            print("   - Perte de granularité")
            print("   - Debugging difficile")
            print("   - Delta fixe")
            print("   - Non-conformité aux webhooks")
        else:
            print("⚠️  Table message_groups non trouvée - migration nécessaire")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 60)
    
    # Approche 3: Hybride (recommandée)
    print("🔄 APPROCHE 3: HYBRIDE (Recommandée)")
    print("=" * 60)
    print("✅ Combine le meilleur des deux:")
    print("   - Messages individuels pour traçabilité")
    print("   - Groupes concaténés pour performance")
    print("   - Analytics flexibles")
    print("   - Debugging possible")
    print("   - Stockage optimisé")
    
    print("\n=== RECOMMANDATION FINALE ===")
    print("🎯 Utiliser l'approche HYBRIDE car elle offre:")
    print("   1. Traçabilité complète (messages individuels)")
    print("   2. Performance optimale (groupes pré-calculés)")
    print("   3. Flexibilité d'analyse")
    print("   4. Facilité de debugging")
    print("   5. Conformité aux standards")
    
    print("\n=== IMPLÉMENTATION ===")
    print("1. Créer la table message_groups (migration SQL)")
    print("2. Modifier le processeur de messages pour l'approche hybride")
    print("3. Ajouter un cron job pour finaliser les groupes expirés")
    print("4. Créer des endpoints pour analyser les deux vues")

if __name__ == "__main__":
    asyncio.run(compare_approaches())





